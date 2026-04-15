from sqlalchemy.orm import relationship
import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class EnrollmentRole(str, enum.Enum):
    student = "student"
    co_teacher = "co_teacher"

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    subject_code = Column(String(20), nullable=False)
    section = Column(String(10), nullable=False)
    semester = Column(String(10), nullable=False)
    join_code = Column(String(6), unique=True, index=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # Default settings as requested in the PRD/Guide
    settings = Column(JSONB, server_default='{"max_drafts": 3, "late_policy": "penalty", "ai_feedback": true}')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    enrollments = relationship("Enrollment", back_populates="classroom", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), index=True, nullable=False)
    role = Column(Enum(EnrollmentRole), nullable=False, default=EnrollmentRole.student)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensures a user cannot join the same classroom twice
    __table_args__ = (
        UniqueConstraint('user_id', 'classroom_id', name='uq_user_classroom'),    
    )
    classroom = relationship("Classroom", back_populates="enrollments")