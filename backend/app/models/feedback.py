import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), index=True, nullable=False)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("rubric_criteria.id"), index=True, nullable=False)
    
    estimated_score = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=False)
    suggested_level = Column(String(50), nullable=True) # "excellent", "good", etc.
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships to easily fetch the parent submission or the rubric criterion
    submission = relationship("Submission", backref="ai_feedbacks")
    criterion = relationship("RubricCriteria")