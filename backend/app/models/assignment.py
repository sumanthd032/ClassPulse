from sqlalchemy.orm import relationship
import uuid  
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Numeric, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True), index=True, nullable=False)
    total_marks = Column(Integer, nullable=False)
    submission_type = Column(Enum(SubmissionType), nullable=False, default=SubmissionType.text)
    max_drafts = Column(Integer, nullable=False, default=3)
    late_policy = Column(Enum(LatePolicy), nullable=False, default=LatePolicy.penalty)
    penalty_per_day = Column(Numeric(5, 2), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    scheduled_publish_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    criteria = relationship("RubricCriteria", back_populates="assignment", cascade="all, delete-orphan")

class RubricCriteria(Base):
    __tablename__ = "rubric_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    max_marks = Column(Integer, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
    # Expected format: {"excellent": "...", "good": "...", "average": "...", "poor": "..."}
    levels = Column(JSONB, nullable=False)
    assignment = relationship("Assignment", back_populates="criteria")