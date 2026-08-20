import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user_id
from .events import publish_event
from .models import Article
from .schemas import ArticleCreate, ArticleUpdate, ArticleOut, ArticleListOut

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _slugify(title: str, article_id: uuid.UUID) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    # suffix with a short id fragment to keep slugs unique without an extra query
    return f"{base}-{str(article_id)[:8]}"


@router.get("", response_model=ArticleListOut)
def list_articles(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None, description="search title/summary/content"),
    category_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    query = db.query(Article)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Article.title.ilike(like), Article.summary.ilike(like), Article.content.ilike(like))
        )
    if category_id:
        query = query.filter(Article.category_id == category_id)

    total = query.count()
    items = (
        query.order_by(Article.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ArticleListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{article_id}", response_model=ArticleOut)
def get_article(article_id: uuid.UUID, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    article = Article(
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        category_id=payload.category_id,
        author_id=current_user_id,
    )
    article.slug = _slugify(payload.title, article.id)
    db.add(article)
    db.commit()
    db.refresh(article)

    publish_event(
        "ARTICLE_PUBLISHED",
        {"article_id": str(article.id), "title": article.title, "author_id": str(current_user_id)},
    )
    return article


@router.put("/{article_id}", response_model=ArticleOut)
def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    if article.author_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the article author")

    if payload.title is not None:
        article.title = payload.title
        article.slug = _slugify(payload.title, article.id)
    if payload.summary is not None:
        article.summary = payload.summary
    if payload.content is not None:
        article.content = payload.content
    if payload.category_id is not None:
        article.category_id = payload.category_id

    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    if article.author_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the article author")
    db.delete(article)
    db.commit()
    return None
