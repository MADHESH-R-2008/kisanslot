import logging
from typing import Optional
from sqlalchemy.orm import Session
from models import Notification, NotificationPreference, NotificationTypeEnum

logger = logging.getLogger("notification_service")

class BaseNotificationProvider:
    def send(self, db: Session, notification: Notification) -> bool:
        raise NotImplementedError

class InAppNotificationProvider(BaseNotificationProvider):
    def send(self, db: Session, notification: Notification) -> bool:
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return True

class FirebaseNotificationProvider(BaseNotificationProvider):
    def __init__(self, fcm_api_key: Optional[str] = None):
        self.fcm_api_key = fcm_api_key

    def send(self, db: Session, notification: Notification) -> bool:
        if self.fcm_api_key:
            logger.info(f"[FCM Push] Sending push notification to user {notification.user_id}: {notification.title}")
        else:
            logger.debug(f"[FCM Push] FCM disabled or no credentials. Skipping push for user {notification.user_id}.")
        return True

class NotificationService:
    def __init__(self):
        self.in_app_provider = InAppNotificationProvider()
        self.firebase_provider = FirebaseNotificationProvider()

    def is_notification_enabled(self, db: Session, user_id: int, notification_type: str) -> bool:
        if not user_id:
            return True
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            return True
        
        # Payment and system security notifications cannot be disabled
        critical_types = [
            NotificationTypeEnum.PAYMENT_PROCESSING.value,
            NotificationTypeEnum.PAYMENT_COMPLETED.value,
            NotificationTypeEnum.PAYMENT_FAILED.value,
            NotificationTypeEnum.SYSTEM.value
        ]
        if notification_type in critical_types:
            return True

        if notification_type in [NotificationTypeEnum.BOOKING_CONFIRMED.value, "BOOKING_CONFIRMED"]:
            return pref.booking_notifications
        elif notification_type in [NotificationTypeEnum.QUEUE_UPDATE.value, NotificationTypeEnum.FARMER_CALLED.value, "QUEUE_UPDATE", "FARMER_CALLED"]:
            return pref.queue_notifications
        elif notification_type in [NotificationTypeEnum.PROCUREMENT_STARTED.value, NotificationTypeEnum.PROCUREMENT_COMPLETED.value, "PROCUREMENT_STARTED", "PROCUREMENT_COMPLETED"]:
            return pref.procurement_notifications
        elif notification_type in [NotificationTypeEnum.CENTRE_UPDATE.value, "CENTRE_UPDATE"]:
            return pref.system_notifications
        return True

    def create_notification(
        self,
        db: Session,
        user_id: Optional[int],
        notification_type: str,
        title: str,
        message: str,
        booking_id: Optional[int] = None,
        centre_id: Optional[int] = None
    ) -> Optional[Notification]:
        if user_id and not self.is_notification_enabled(db, user_id, notification_type):
            logger.info(f"Notification {notification_type} muted by user preferences for user_id={user_id}")
            return None

        notif = Notification(
            user_id=user_id,
            booking_id=booking_id,
            centre_id=centre_id,
            type=notification_type,
            title=title,
            message=message,
            is_read=False
        )

        self.in_app_provider.send(db, notif)
        self.firebase_provider.send(db, notif)
        return notif

# Convenience global singleton
notification_service = NotificationService()

def create_notification(
    db: Session,
    user_id: Optional[int],
    notification_type: str,
    title: str,
    message: str,
    booking_id: Optional[int] = None,
    centre_id: Optional[int] = None
) -> Optional[Notification]:
    return notification_service.create_notification(
        db=db,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        booking_id=booking_id,
        centre_id=centre_id
    )
