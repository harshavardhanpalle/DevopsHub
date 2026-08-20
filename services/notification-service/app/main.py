from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401
from .routes_notifications import router as notifications_router
from .sqs_consumer import start_consumer_thread, stop_consumer

app = FastAPI(title="notification-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    start_consumer_thread()


@app.on_event("shutdown")
def on_shutdown():
    # Signals the SQS poll loop to stop after its current iteration so the
    # process doesn't rely solely on the daemon thread being killed when
    # the container exits.
    stop_consumer()


@app.get("/health")
def health():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "service": "notification-service", "database": db_ok}
