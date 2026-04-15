"""
Gradebook service — full student × grade matrix for a teacher.

Provides:
  - get_gradebook()  → structured list of every enrolled student + their grade
  - generate_pdf()   → ReportLab PDF bytes for download
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.assignment import Assignment
from app.models.classroom import Classroom, Enrollment, EnrollmentRole
from app.models.grade import Grade
from app.models.submission import Submission
from app.models.user import User


# ---------------------------------------------------------------------------
# Data shape
# ---------------------------------------------------------------------------
class GradebookEntry:
    __slots__ = (
        "student_id", "student_name", "student_email",
        "has_submitted", "is_late", "score", "max_marks",
        "percentage", "letter_grade", "is_released", "is_ai_graded",
    )

    def __init__(
        self,
        student_id: UUID,
        student_name: str,
        student_email: str,
        has_submitted: bool,
        is_late: bool,
        score: Optional[int],
        max_marks: int,
        is_released: bool,
        is_ai_graded: bool,
    ) -> None:
        self.student_id = student_id
        self.student_name = student_name
        self.student_email = student_email
        self.has_submitted = has_submitted
        self.is_late = is_late
        self.score = score
        self.max_marks = max_marks
        self.percentage = round(score / max_marks * 100, 1) if score is not None and max_marks else None
        self.letter_grade = _letter_grade(self.percentage)
        self.is_released = is_released
        self.is_ai_graded = is_ai_graded

    def to_dict(self) -> dict:
        return {
            "student_id": str(self.student_id),
            "student_name": self.student_name,
            "student_email": self.student_email,
            "has_submitted": self.has_submitted,
            "is_late": self.is_late,
            "score": self.score,
            "max_marks": self.max_marks,
            "percentage": self.percentage,
            "letter_grade": self.letter_grade,
            "is_released": self.is_released,
            "is_ai_graded": self.is_ai_graded,
        }


def _letter_grade(pct: Optional[float]) -> Optional[str]:
    if pct is None:
        return None
    if pct >= 90:
        return "O"   # Outstanding
    if pct >= 75:
        return "A"
    if pct >= 60:
        return "B"
    if pct >= 50:
        return "C"
    if pct >= 40:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------
async def _get_assignment_and_verify(
    db: AsyncSession, assignment_id: UUID, user_id: UUID
) -> tuple[Assignment, Classroom]:
    assign_res = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = assign_res.scalars().first()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    enroll_res = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == assignment.classroom_id,
            Enrollment.user_id == user_id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not enroll_res.scalars().first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers only")

    class_res = await db.execute(select(Classroom).where(Classroom.id == assignment.classroom_id))
    classroom = class_res.scalars().first()
    return assignment, classroom


async def get_gradebook(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> List[dict]:
    """
    Returns one entry per enrolled student with their submission + grade status.
    Visible to classroom teachers only.
    """
    assignment, _ = await _get_assignment_and_verify(db, assignment_id, current_user.id)

    # All students enrolled in this classroom
    students_res = await db.execute(
        select(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .where(
            Enrollment.classroom_id == assignment.classroom_id,
            Enrollment.role == EnrollmentRole.student,
        )
        .order_by(User.full_name)
    )
    students = students_res.scalars().all()

    # Final submissions for this assignment keyed by student_id
    subs_res = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.is_final == True,  # noqa: E712
        )
    )
    subs_by_student: dict[UUID, Submission] = {
        s.student_id: s for s in subs_res.scalars().all()
    }

    # Grades keyed by submission_id
    if subs_by_student:
        sub_ids = list(subs_by_student[sid].id for sid in subs_by_student)
        grades_res = await db.execute(
            select(Grade).where(Grade.submission_id.in_(sub_ids))
        )
        grades_by_sub: dict[UUID, Grade] = {
            g.submission_id: g for g in grades_res.scalars().all()
        }
    else:
        grades_by_sub = {}

    entries = []
    for student in students:
        sub = subs_by_student.get(student.id)
        grade = grades_by_sub.get(sub.id) if sub else None
        entry = GradebookEntry(
            student_id=student.id,
            student_name=student.full_name,
            student_email=student.email,
            has_submitted=sub is not None,
            is_late=sub.is_late if sub else False,
            score=grade.total_score if grade else None,
            max_marks=assignment.total_marks,
            is_released=grade.is_released if grade else False,
            is_ai_graded=(grade is not None and str(grade.grader_id) == str(sub.student_id)) if sub else False,
        )
        entries.append(entry.to_dict())

    return entries


async def generate_pdf(
    db: AsyncSession, assignment_id: UUID, current_user: User
) -> bytes:
    """
    Generates a PDF gradebook using ReportLab and returns the raw bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable,
    )

    assignment, classroom = await _get_assignment_and_verify(db, assignment_id, current_user.id)
    entries = await get_gradebook(db, assignment_id, current_user)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    VIOLET = colors.HexColor("#7C3AED")
    DARK = colors.HexColor("#18181B")
    LIGHT_GRAY = colors.HexColor("#F4F4F5")
    MID_GRAY = colors.HexColor("#E4E4E7")
    GREEN = colors.HexColor("#16A34A")
    RED = colors.HexColor("#DC2626")
    AMBER = colors.HexColor("#D97706")
    BLUE = colors.HexColor("#2563EB")

    def grade_color(letter: Optional[str]) -> colors.Color:
        if letter in ("O", "A"):
            return GREEN
        if letter == "B":
            return BLUE
        if letter == "C":
            return AMBER
        return RED

    header_style = ParagraphStyle(
        "header", parent=styles["Normal"],
        fontSize=18, textColor=DARK, fontName="Helvetica-Bold", spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#71717A"), spaceAfter=2,
    )
    caption_style = ParagraphStyle(
        "caption", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#A1A1AA"),
    )

    # -----------------------------------------------------------------------
    # Summary stats
    # -----------------------------------------------------------------------
    graded = [e for e in entries if e["score"] is not None]
    avg_pct = round(sum(e["percentage"] for e in graded) / len(graded), 1) if graded else None
    highest = max((e["score"] for e in graded), default=None)
    lowest = min((e["score"] for e in graded), default=None)
    submitted_count = sum(1 for e in entries if e["has_submitted"])
    released_count = sum(1 for e in entries if e["is_released"])

    # -----------------------------------------------------------------------
    # Build content
    # -----------------------------------------------------------------------
    story = []

    # Title block
    story.append(Paragraph(f"Gradebook — {assignment.title}", header_style))
    story.append(Paragraph(
        f"{classroom.name} &nbsp;·&nbsp; {classroom.subject_code} &nbsp;·&nbsp; "
        f"Section {classroom.section} &nbsp;·&nbsp; Semester {classroom.semester}",
        sub_style,
    ))
    story.append(Paragraph(
        f"Max marks: {assignment.total_marks} &nbsp;·&nbsp; "
        f"Deadline: {assignment.deadline.strftime('%d %b %Y, %I:%M %p')} &nbsp;·&nbsp; "
        f"Generated: {datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p UTC')}",
        caption_style,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=VIOLET, spaceAfter=0.4 * cm))

    # Summary bar
    summary_data = [
        ["Total Students", "Submitted", "Graded", "Released", "Class Avg", "Highest", "Lowest"],
        [
            str(len(entries)),
            str(submitted_count),
            str(len(graded)),
            str(released_count),
            f"{avg_pct}%" if avg_pct is not None else "—",
            f"{highest}/{assignment.total_marks}" if highest is not None else "—",
            f"{lowest}/{assignment.total_marks}" if lowest is not None else "—",
        ],
    ]
    summary_table = Table(summary_data, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VIOLET),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.4 * cm))

    # Main grade table
    col_headers = ["#", "Student Name", "Email", "Submitted", "Late", "Score", "/ Max", "%", "Grade", "Status"]
    table_data = [col_headers]

    for i, e in enumerate(entries, start=1):
        status_text = "Released" if e["is_released"] else ("AI Suggested" if e["is_ai_graded"] else ("Graded" if e["score"] is not None else "—"))
        row = [
            str(i),
            e["student_name"],
            e["student_email"],
            "✓" if e["has_submitted"] else "✗",
            "Yes" if e["is_late"] else "No",
            str(e["score"]) if e["score"] is not None else "—",
            str(e["max_marks"]),
            f"{e['percentage']}%" if e["percentage"] is not None else "—",
            e["letter_grade"] or "—",
            status_text,
        ]
        table_data.append(row)

    col_widths = [1*cm, 5*cm, 6*cm, 1.8*cm, 1.5*cm, 1.8*cm, 1.5*cm, 2*cm, 1.8*cm, 3.2*cm]
    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Build row-level styles dynamically
    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (2, -1), "LEFT"),  # Name + email left-aligned
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GRAY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, MID_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]

    for i, e in enumerate(entries, start=1):
        # Submitted col colour
        submitted_col = 3
        late_col = 4
        grade_col = 8
        status_col = 9

        if e["has_submitted"]:
            style_cmds.append(("TEXTCOLOR", (submitted_col, i), (submitted_col, i), GREEN))
        else:
            style_cmds.append(("TEXTCOLOR", (submitted_col, i), (submitted_col, i), RED))

        if e["is_late"]:
            style_cmds.append(("TEXTCOLOR", (late_col, i), (late_col, i), RED))

        if e["letter_grade"]:
            style_cmds.append(("TEXTCOLOR", (grade_col, i), (grade_col, i), grade_color(e["letter_grade"])))
            style_cmds.append(("FONTNAME", (grade_col, i), (grade_col, i), "Helvetica-Bold"))

        if e["is_released"]:
            style_cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), GREEN))
        elif e["is_ai_graded"]:
            style_cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), VIOLET))
        elif e["score"] is not None:
            style_cmds.append(("TEXTCOLOR", (status_col, i), (status_col, i), AMBER))

    main_table.setStyle(TableStyle(style_cmds))
    story.append(main_table)

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "Grade scale: O ≥ 90%  |  A ≥ 75%  |  B ≥ 60%  |  C ≥ 50%  |  D ≥ 40%  |  F < 40%  "
        "   Status: Released = visible to students  |  AI Suggested = pending teacher review",
        caption_style,
    ))

    doc.build(story)
    return buf.getvalue()
