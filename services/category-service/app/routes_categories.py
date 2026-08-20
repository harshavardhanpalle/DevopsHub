import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user_id
from .models import Category
from .schemas import CategoryCreate, CategoryOut, CategoryListOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@router.get("", response_model=CategoryListOut)
def list_categories(db: Session = Depends(get_db), q: Optional[str] = Query(default=None)):
    query = db.query(Category)
    if q:
        query = query.filter(Category.name.ilike(f"%{q}%"))
    items = query.order_by(Category.name.asc()).all()
    return CategoryListOut(items=items, total=len(items))


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    slug = _slugify(payload.name)
    existing = db.query(Category).filter(
        (Category.name == payload.name) | (Category.slug == slug)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")

    category = Category(name=payload.name, slug=slug, description=payload.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
