"""
Classroom service — business logic for classroom CRUD and enrollment.
"""
import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.classroom import Classroom, Enrollment, EnrollmentRole
from app.models.user import User, UserRole
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate


async def _generate_unique_join_code(db: AsyncSession) -> str:
    """
    Generates a 6-character uppercase hex join code that is guaranteed unique.
    Loops until no collision is found (extremely unlikely after the first try).
    """
    while True:
        code = secrets.token_hex(3).upper()
        result = await db.execute(select(Classroom).where(Classroom.join_code == code))
        if not result.scalars().first():
            return code


async def create_classroom(
    db: AsyncSession, data: ClassroomCreate, current_user: User
) -> Classroom:
    """
    Creates a classroom and auto-enrolls the creator as `co_teacher`.

    Only teachers and admins can create classrooms.
    The join code is auto-generated and guaranteed unique.
    """
    if current_user.role == UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot create classrooms",
        )

    join_code = await _generate_unique_join_code(db)

    classroom = Classroom(
        name=data.name,
        subject_code=data.subject_code,
        section=data.section,
        semester=data.semester,
        join_code=join_code,
        created_by=current_user.id,
    )
    db.add(classroom)
    await db.flush()  # Generates classroom.id before we use it below

    # Auto-enroll creator as co_teacher so they appear in their own class list
    enrollment = Enrollment(
        user_id=current_user.id,
        classroom_id=classroom.id,
        role=EnrollmentRole.co_teacher,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(classroom)
    return classroom


async def join_classroom(db: AsyncSession, join_code: str, current_user: User) -> Classroom:
    """
    Enrolls `current_user` as a student in the classroom with the given join code.

    Returns 404 if the code is invalid.
    Returns 409 if the user is already enrolled.
    """
    result = await db.execute(
        select(Classroom).where(Classroom.join_code == join_code.upper())
    )
    classroom = result.scalars().first()

    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No classroom found with that join code",
        )

    enrollment = Enrollment(
        user_id=current_user.id,
        classroom_id=classroom.id,
        role=EnrollmentRole.student,
    )
    db.add(enrollment)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already enrolled in this classroom",
        )

    return classroom


async def get_user_classrooms(db: AsyncSession, current_user: User):
    """
    Returns all enrollment records (with nested classroom data) for `current_user`.
    Used to populate the dashboard classroom list.
    """
    result = await db.execute(
        select(Enrollment)
        .options(joinedload(Enrollment.classroom))
        .where(Enrollment.user_id == current_user.id)
    )
    return result.scalars().all()


async def get_classroom_or_404(
    db: AsyncSession, classroom_id: UUID, current_user: User
) -> Classroom:
    """
    Returns a single classroom.
    Raises 404 if it doesn't exist.
    Raises 403 if the caller is not enrolled.
    """
    result = await db.execute(
        select(Classroom).where(Classroom.id == classroom_id)
    )
    classroom = result.scalars().first()

    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    # Verify the caller is enrolled
    enroll_result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == current_user.id,
        )
    )
    if not enroll_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this classroom",
        )

    return classroom


async def update_classroom(
    db: AsyncSession,
    classroom_id: UUID,
    data: ClassroomUpdate,
    current_user: User,
) -> Classroom:
    """
    Partially updates a classroom.
    Only the teacher who created the classroom can call this.
    Settings fields are merged into the existing JSONB column.
    """
    result = await db.execute(
        select(Classroom).where(Classroom.id == classroom_id)
    )
    classroom = result.scalars().first()

    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    if str(classroom.created_by) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the classroom creator can update it",
        )

    # Update top-level fields if provided
    if data.name is not None:
        classroom.name = data.name

    # Merge settings changes into the JSONB column
    settings_patch = {}
    if data.max_drafts is not None:
        settings_patch["max_drafts"] = data.max_drafts
    if data.late_policy is not None:
        settings_patch["late_policy"] = data.late_policy
    if data.ai_feedback is not None:
        settings_patch["ai_feedback"] = data.ai_feedback

    if settings_patch:
        # Merge with existing settings (avoid overwriting unrelated keys)
        current_settings = dict(classroom.settings or {})
        current_settings.update(settings_patch)
        classroom.settings = current_settings

    await db.commit()
    await db.refresh(classroom)
    return classroom


async def get_enrolled_students(
    db: AsyncSession, classroom_id: UUID, current_user: User
):
    """
    Returns the student roster for the given classroom.
    Only the teacher (co_teacher role) can access this.

    Returns a list of dicts with user_id, full_name, email, joined_at.
    """
    # Verify caller is a teacher in this classroom
    enroll_result = await db.execute(
        select(Enrollment).where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.user_id == current_user.id,
            Enrollment.role == EnrollmentRole.co_teacher,
        )
    )
    if not enroll_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view the student roster",
        )

    # Join enrollments with users to get student details
    from app.models.user import User as UserModel
    students_result = await db.execute(
        select(Enrollment, UserModel)
        .join(UserModel, Enrollment.user_id == UserModel.id)
        .where(
            Enrollment.classroom_id == classroom_id,
            Enrollment.role == EnrollmentRole.student,
        )
        .order_by(UserModel.full_name)
    )

    rows = students_result.all()
    return [
        {
            "user_id": row.Enrollment.user_id,
            "full_name": row.User.full_name,
            "email": row.User.email,
            "joined_at": row.Enrollment.joined_at,
        }
        for row in rows
    ]
