"""Submission ORM model — covers both drafts and the final answer."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assignments.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Submission content — one or both depending on assignment.submission_type
    content = Column(Text, nullable=True)            # Plain text / Markdown answer
    file_url = Column(String(500), nullable=True)    # Path or URL to uploaded file

    # Draft / final state
    is_final = Column(Boolean, default=False, nullable=False)
    draft_number = Column(Integer, nullable=False, default=1)
    is_late = Column(Boolean, default=False, nullable=False)

    # Plagiarism / similarity — populated asynchronously by the similarity worker
    similarity_score = Column(Float, nullable=True)      # Highest match ratio found (0-1)
    similarity_flagged = Column(Boolean, default=False, nullable=False)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    assignment = relationship("Assignment", backref="submissions")
    student = relationship("User", backref="submissions")

    __table_args__ = (
        # Composite index for the most common query: "all submissions for this
        # student on this assignment, filtered by draft vs. final"
        Index("ix_submissions_assignment_student_final", "assignment_id", "student_id", "is_final"),
        # Partial unique index: a student may have many drafts (is_final=False)
        # but only ONE final submission (is_final=True)
        Index(
            "uq_final_submission",
            "assignment_id",
            "student_id",
            unique=True,
            postgresql_where=(is_final == True),  # noqa: E712
        ),
    )
