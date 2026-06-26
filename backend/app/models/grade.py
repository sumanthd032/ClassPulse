import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Grade(Base):
    __tablename__ = "grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # A submission can only have ONE official grade, so unique=True
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), unique=True, nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), index=True, nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    grader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    total_score = Column(Integer, nullable=False)
    teacher_comments = Column(Text, nullable=True)
    
    # CRITICAL: Grades are never auto-released to students
    is_released = Column(Boolean, default=False, nullable=False)
    
    graded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships for easy querying
    submission = relationship("Submission", backref="official_grade")
    assignment = relationship("Assignment", backref="grades")
    # We have to specify foreign_keys here because there are two User IDs in this table!
    student = relationship("User", foreign_keys=[student_id], backref="received_grades")
    grader = relationship("User", foreign_keys=[grader_id], backref="given_grades")