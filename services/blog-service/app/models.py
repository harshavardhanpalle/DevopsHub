import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(280), unique=True, index=True, nullable=False)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    # Foreign keys to other services' data are stored as plain UUIDs, not
    # SQLAlchemy relationships -- blog-service does not own users or
    # categories, it only references their IDs (set by category-service /
    # user-service respectively). This matches the "avoid duplicate
    # ownership" rule in the assignment.
    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
