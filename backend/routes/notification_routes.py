import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Notification, NotificationPreference, RoleEnum
from dependencies import get_current_user
from schemas import (
    NotificationResponse,
    PaginatedNotificationResponse,
    NotificationUnreadCountResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def build_user_notifications_query(db: Session, user: dict):
    user_id = user["user_id"]
    role = user["role"]
    centre_id = user.get("centre_id")

    query = db.query(Notification)

    if role == RoleEnum.FARMER.value:
        query = query.filter(Notification.user_id == user_id)
    elif role == RoleEnum.CENTRE_OPERATOR.value:
        conditions = [Notification.user_id == user_id]
        if centre_id:
            conditions.append(Notification.centre_id == centre_id)
        query = query.filter(or_(*conditions))
    elif role in [RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value]:
        query = query.filter(
            or_(
                Notification.user_id == user_id,
                Notification.type.in_(["SYSTEM", "CENTRE_UPDATE"]),
                Notification.user_id.is_(None),
            )
        )
    else:
        query = query.filter(Notification.user_id == user_id)

    return query


@router.get("", response_model=PaginatedNotificationResponse)
@router.get("/", response_model=PaginatedNotificationResponse)
def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get notifications for the logged-in user with security filtering and pagination.
    """
    base_query = build_user_notifications_query(db, user)

    unread_count = base_query.filter(Notification.is_read == False).count()

    filtered_query = base_query
    if unread_only:
        filtered_query = filtered_query.filter(Notification.is_read == False)

    total = filtered_query.count()
    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit

    items = (
        filtered_query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return PaginatedNotificationResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the unread notification count for the current logged-in user.
    """
    base_query = build_user_notifications_query(db, user)
    unread_count = base_query.filter(Notification.is_read == False).count()
    return NotificationUnreadCountResponse(unread_count=unread_count)


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a specific notification as read for the current user.
    """
    base_query = build_user_notifications_query(db, user)
    notification = base_query.filter(Notification.id == notification_id).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied",
        )

    notification.is_read = True
    notification.updated_at = datetime.utcnow()
    db.commit()
    return {
        "message": "Notification marked as read",
        "notification_id": notification_id,
    }


@router.put("/read-all")
def mark_all_notifications_read(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications for the current user as read.
    """
    base_query = build_user_notifications_query(db, user)
    unread_notifications = base_query.filter(Notification.is_read == False).all()

    for notif in unread_notifications:
        notif.is_read = True
        notif.updated_at = datetime.utcnow()

    db.commit()
    return {
        "message": "All notifications marked as read",
        "count": len(unread_notifications),
    }


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user notification preferences.
    """
    user_id = user["user_id"]
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    update_data: NotificationPreferenceUpdate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user notification preferences.
    """
    user_id = user["user_id"]
    pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)

    if update_data.booking_notifications is not None:
        pref.booking_notifications = update_data.booking_notifications
    if update_data.queue_notifications is not None:
        pref.queue_notifications = update_data.queue_notifications
    if update_data.procurement_notifications is not None:
        pref.procurement_notifications = update_data.procurement_notifications
    if update_data.payment_notifications is not None:
        pref.payment_notifications = update_data.payment_notifications
    if update_data.system_notifications is not None:
        pref.system_notifications = update_data.system_notifications

    pref.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(pref)
    return pref
