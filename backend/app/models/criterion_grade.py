import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CriterionGrade(Base):
    __tablename__ = "criterion_grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id", ondelete="CASCADE"), index=True, nullable=False)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("rubric_criteria.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    grade = relationship("Grade", backref="criterion_grades")
    criterion = relationship("RubricCriteria", backref="criterion_grades")
