import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListOut(BaseModel):
    items: List[NotificationOut]
    total: int
    unread_count: int
