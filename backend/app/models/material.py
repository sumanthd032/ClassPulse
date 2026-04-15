import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class MaterialType(str, enum.Enum):
    link = "link"
    file = "file"
    video = "video"
    document = "document"


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="CASCADE"), index=True, nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    material_type = Column(
        Enum(MaterialType, native_enum=False, name="material_type_enum"),
        nullable=False,
        default=MaterialType.link,
    )
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User", backref="materials")
