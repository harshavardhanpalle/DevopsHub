from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401
from .routes_categories import router as categories_router

app = FastAPI(title="category-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    # Seed a small default taxonomy matching the existing frontend's
    # hardcoded tags (Linux, AWS, Terraform, Docker, Kubernetes, CI/CD) so
    # blog.html has real categories to filter by from first boot.
    from .models import Category
    import re

    db = SessionLocal()
    try:
        defaults = ["Linux", "AWS", "Terraform", "Docker", "Kubernetes", "CI/CD"]
        for name in defaults:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            if not db.query(Category).filter(Category.slug == slug).first():
                db.add(Category(name=name, slug=slug))
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "service": "category-service", "database": db_ok}
