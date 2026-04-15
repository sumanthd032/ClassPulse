"""
Auto-grading Celery task.

Triggered when a student submits their FINAL submission.
Uses the Gemini LLM to evaluate the submission against each rubric criterion
and creates a Grade + CriterionGrade record (is_released=False so the teacher
reviews before publishing to the student).

The teacher is notified via DB notification so they can review, adjust, and release.
"""
import json
import logging
from uuid import UUID as PyUUID

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assignment import Assignment, RubricCriteria
from app.models.criterion_grade import CriterionGrade
from app.models.grade import Grade
from app.models.submission import Submission
from app.utils.llm_client import call_llm
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

_SYSTEM_PROMPT = (
    "You are an expert academic grader for an Indian engineering college. "
    "Evaluate the student's FINAL submission against each rubric criterion and assign marks. "
    "For each criterion return:\n"
    "  - criterion_id (copy from input exactly)\n"
    "  - score (integer between 0 and max_marks inclusive)\n"
    "  - comment (1-2 sentences justifying the score — be fair and constructive)\n"
    "  - suggested_level ('excellent' | 'good' | 'average' | 'poor')\n"
    "Be objective and consistent. Partial credit is encouraged. "
    "Output ONLY a valid JSON array — one object per criterion, no extra text."
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def auto_grade_submission(self, submission_id: str) -> str:
    """
    Auto-grades a final submission using the LLM.

    Creates a Grade row (is_released=False) and per-criterion CriterionGrade rows.
    The teacher must review and release the grade manually.

    Returns a status string: "success", "skipped:*", or raises for retry.
    """
    db = _SessionLocal()
    try:
        # ----------------------------------------------------------------
        # 1. Load data
        # ----------------------------------------------------------------
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.warning("auto_grade: submission %s not found", submission_id)
            return "skipped:not_found"

        if not submission.is_final:
            logger.info("auto_grade: submission %s is not final — skipping", submission_id)
            return "skipped:not_final"

        if not submission.content or not submission.content.strip():
            logger.info("auto_grade: submission %s has no text content — skipping", submission_id)
            return "skipped:no_content"

        # Skip if already graded (e.g. teacher graded manually before worker ran)
        existing_grade = db.query(Grade).filter(Grade.submission_id == submission.id).first()
        if existing_grade:
            logger.info("auto_grade: grade already exists for submission %s", submission_id)
            return "skipped:already_graded"

        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        if not assignment:
            return "skipped:no_assignment"

        rubric_criteria = (
            db.query(RubricCriteria)
            .filter(RubricCriteria.assignment_id == assignment.id)
            .order_by(RubricCriteria.order_index)
            .all()
        )

        if not rubric_criteria:
            logger.info("auto_grade: assignment %s has no rubric — skipping", assignment.id)
            return "skipped:no_rubric"

        # ----------------------------------------------------------------
        # 2. Call the LLM
        # ----------------------------------------------------------------
        rubric_data = [
            {
                "criterion_id": str(c.id),
                "name": c.name,
                "max_marks": c.max_marks,
                "levels": c.levels,
            }
            for c in rubric_criteria
        ]

        user_prompt = (
            f"Assignment: {assignment.title}\n"
            f"Description: {assignment.description or 'No description provided.'}\n\n"
            f"Rubric criteria:\n{json.dumps(rubric_data, indent=2)}\n\n"
            f"Student's final submission:\n{submission.content}\n\n"
            "Return a JSON array — one object per criterion with exactly these keys: "
            "criterion_id, score, comment, suggested_level"
        )

        try:
            evaluations = call_llm(_SYSTEM_PROMPT, user_prompt)
        except Exception as exc:
            import httpx as _httpx
            if isinstance(exc, _httpx.HTTPStatusError) and exc.response is not None and exc.response.status_code == 429:
                logger.warning("Gemini 429 for auto_grade %s — retrying in 60s", submission_id)
                raise self.retry(exc=exc, countdown=60)
            logger.error("auto_grade LLM call failed for submission %s: %s", submission_id, exc)
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

        # ----------------------------------------------------------------
        # 3. Build lookup: criterion_id → evaluation
        # ----------------------------------------------------------------
        eval_map: dict[str, dict] = {}
        for item in evaluations:
            cid = str(item.get("criterion_id", ""))
            if cid:
                eval_map[cid] = item

        # ----------------------------------------------------------------
        # 4. Compute total score
        # ----------------------------------------------------------------
        total_score = 0
        for c in rubric_criteria:
            ev = eval_map.get(str(c.id), {})
            raw_score = ev.get("score", 0)
            # Clamp to [0, max_marks]
            score = max(0, min(int(raw_score), c.max_marks))
            total_score += score

        # ----------------------------------------------------------------
        # 5. Create Grade row (unreleased — teacher must review first)
        # ----------------------------------------------------------------
        # We use a sentinel grader_id: the student's own ID tagged as AI-graded.
        # In the UI we detect grader_id == student_id and show "AI suggested".
        grade = Grade(
            submission_id=submission.id,
            assignment_id=assignment.id,
            student_id=submission.student_id,
            grader_id=submission.student_id,  # sentinel: AI-graded
            total_score=total_score,
            teacher_comments=(
                "⚡ AI-suggested grade — please review and adjust before releasing."
            ),
            is_released=False,
        )
        db.add(grade)
        db.flush()  # get grade.id without committing

        # ----------------------------------------------------------------
        # 6. Create CriterionGrade rows
        # ----------------------------------------------------------------
        for c in rubric_criteria:
            ev = eval_map.get(str(c.id), {})
            raw_score = ev.get("score", 0)
            score = max(0, min(int(raw_score), c.max_marks))
            comment = ev.get("comment", "")
            db.add(
                CriterionGrade(
                    grade_id=grade.id,
                    criterion_id=c.id,
                    score=score,
                    comment=comment,
                )
            )

        db.commit()

        # ----------------------------------------------------------------
        # 7. Notify the teacher(s) via DB notification
        # ----------------------------------------------------------------
        from app.models.classroom import Enrollment, EnrollmentRole
        from app.models.notification import Notification

        teachers = (
            db.query(Enrollment)
            .filter(
                Enrollment.classroom_id == assignment.classroom_id,
                Enrollment.role == EnrollmentRole.co_teacher,
            )
            .all()
        )
        for enrollment in teachers:
            db.add(
                Notification(
                    user_id=enrollment.user_id,
                    type="AUTO_GRADE_READY",
                    title="AI grade suggestion ready",
                    message=(
                        f"A final submission for '{assignment.title}' has been auto-graded "
                        f"({total_score}/{assignment.total_marks}). "
                        "Review and release when ready."
                    ),
                )
            )
        db.commit()

        logger.info(
            "auto_grade: submission %s graded %d/%d",
            submission_id,
            total_score,
            assignment.total_marks,
        )
        return "success"

    except Exception as exc:
        db.rollback()
        logger.exception("auto_grade_submission failed for %s", submission_id)
        raise exc
    finally:
        db.close()
