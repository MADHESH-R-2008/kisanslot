from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Notification, Farmer
from auth import get_current_farmer
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current farmer."""
    notifications = db.query(Notification).filter(
        Notification.user_id == farmer.id
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == farmer.id
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

@router.put("/read-all")
def mark_all_notifications_read(
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """Mark all notifications for the farmer as read."""
    db.query(Notification).filter(
        Notification.user_id == farmer.id,
        Notification.is_read == False
    ).update({Notification.is_read: True})
    db.commit()
    return {"message": "All notifications marked as read"}

class DeviceTokenRequest(BaseModel):
    token: str

@router.post("/device-token")
def register_device_token(
    req: DeviceTokenRequest,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db)
):
    """
    Placeholder endpoint to store a device token for future Firebase push notifications.
    Currently not persisted; will be implemented later.
    """
    # TODO: Save token to a new table if needed.
    return {"message": "Device token received (placeholder)"}
