import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    summary: Optional[str] = Field(default=None, max_length=500)
    content: str = Field(min_length=1)
    category_id: Optional[uuid.UUID] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    summary: Optional[str] = Field(default=None, max_length=500)
    content: Optional[str] = None
    category_id: Optional[uuid.UUID] = None


class ArticleOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    summary: Optional[str] = None
    content: str
    author_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleListOut(BaseModel):
    items: List[ArticleOut]
    total: int
    page: int
    page_size: int
