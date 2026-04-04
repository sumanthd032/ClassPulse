import uuid
from datetime import datetime

from sqlalchemy import Text, String, DateTime, ForeignKey, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        # Only one final submission per student per assignment
        UniqueConstraint("assignment_id", "student_id", name="uq_final_submission",
                         postgresql_where="is_final = true"),
        Index("ix_submissions_assignment_student", "assignment_id", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    draft_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
