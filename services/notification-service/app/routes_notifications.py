import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user_id
from .models import Notification
from .schemas import NotificationOut, NotificationListOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
def list_notifications(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    query = db.query(Notification).filter(Notification.user_id == current_user_id)
    items = query.order_by(Notification.created_at.desc()).all()
    unread = query.filter(Notification.is_read.is_(False)).count()
    return NotificationListOut(items=items, total=len(items), unread_count=unread)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user_id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
