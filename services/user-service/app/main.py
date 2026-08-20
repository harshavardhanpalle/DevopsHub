from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401  (ensures models are registered on Base)
from .routes_auth import router as auth_router
from .routes_users import router as users_router

app = FastAPI(title="user-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)


@app.on_event("startup")
def on_startup():
    # Simple create-all for Stage 1. See migrations/ for the SQL migration
    # equivalent used by fresh deployments / documented in PROJECT_AUDIT.md.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "service": "user-service", "database": db_ok}
