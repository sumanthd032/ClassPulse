"""
Plagiarism / Similarity Check Celery task.

Triggered when a student submits their final answer.

Algorithm: TF-IDF cosine similarity (scikit-learn).
  - Chosen for speed: < 1 second on 300 submissions on modest hardware.
  - No external API call or cost.
  - Catches paraphrasing better than simple sequence matching.
  - Threshold: 80% cosine similarity flags the pair.

When a match is found:
  1. The submission's `similarity_score` and `similarity_flagged` columns are updated.
  2. A PLAGIARISM_FLAG notification is sent to the teacher who created the assignment.
"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assignment import Assignment
from app.models.notification import Notification
from app.models.submission import Submission
from app.utils.similarity import find_highest_match
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_SIMILARITY_THRESHOLD = 0.80  # Flag if TF-IDF cosine similarity >= 80%


@celery_app.task
def check_plagiarism(submission_id: str) -> str:
    """
    Runs a TF-IDF similarity check on a final submission against all other
    final submissions for the same assignment.

    Args:
        submission_id: UUID string of the target Submission.

    Returns:
        "flagged", "clean", or a skip reason string.
    """
    logger.info("Similarity check started for submission %s", submission_id)
    db = _SessionLocal()

    try:
        target = db.query(Submission).filter(Submission.id == submission_id).first()
        if not target:
            return "skipped:not_found"
        if not target.content:
            return "skipped:no_content"
        if not target.is_final:
            return "skipped:not_final"

        # Fetch all OTHER final text submissions for the same assignment
        others = (
            db.query(Submission)
            .filter(
                Submission.assignment_id == target.assignment_id,
                Submission.id != target.id,
                Submission.is_final == True,   # noqa: E712
                Submission.content != None,    # noqa: E711
            )
            .all()
        )

        if not others:
            logger.info("No other submissions to compare — submission %s is clean", submission_id)
            target.similarity_score = 0.0
            target.similarity_flagged = False
            db.commit()
            return "clean:no_others"

        # Run TF-IDF similarity
        candidates = [(str(s.id), s.content) for s in others]
        best_score, matching_id = find_highest_match(
            target.content, candidates, threshold=_SIMILARITY_THRESHOLD
        )

        target.similarity_score = round(best_score, 4)
        target.similarity_flagged = matching_id is not None

        if matching_id:
            pct = int(best_score * 100)
            logger.warning(
                "Plagiarism flagged: submission=%s matches=%s score=%d%%",
                submission_id,
                matching_id,
                pct,
            )

            assignment = db.query(Assignment).filter(
                Assignment.id == target.assignment_id
            ).first()

            # Notify the teacher who created the assignment
            db.add(
                Notification(
                    user_id=str(assignment.created_by),
                    type="PLAGIARISM_FLAG",
                    title="Plagiarism Alert",
                    message=(
                        f"High similarity ({pct}%) detected between two submissions "
                        f"on '{assignment.title}'."
                    ),
                )
            )
            db.commit()
            return f"flagged:{pct}%"

        db.commit()
        logger.info("Submission %s is clean (best score: %.2f)", submission_id, best_score)
        return "clean"

    except Exception as exc:
        db.rollback()
        logger.exception("Plagiarism check failed for submission %s", submission_id)
        raise exc
    finally:
        db.close()
