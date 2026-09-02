from sqlalchemy.orm import Session
from models import Notification

def send_notification(db: Session, user_id: int, title: str, message: str, type_str: str = "INFO"):
    """
    Saves a notification to the database.
    In a real-world scenario, this would also trigger FCM (Firebase Cloud Messaging).
    """
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type_str
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
