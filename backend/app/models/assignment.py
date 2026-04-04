import uuid
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum as SAEnum, DateTime, ForeignKey, Integer, Boolean, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class SubmissionType(str, enum.Enum):
    text = "text"
    file = "file"
    both = "both"


class LatePolicy(str, enum.Enum):
    block = "block"
    penalty = "penalty"
    allow = "allow"


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    submission_type: Mapped[SubmissionType] = mapped_column(
        SAEnum(SubmissionType), nullable=False, default=SubmissionType.text
    )
    max_drafts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    late_policy: Mapped[LatePolicy] = mapped_column(
        SAEnum(LatePolicy), nullable=False, default=LatePolicy.penalty
    )
    penalty_per_day: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # JSONB: { excellent: "...", good: "...", average: "...", poor: "..." }
    levels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {
        "excellent": "", "good": "", "average": "", "poor": ""
    })
