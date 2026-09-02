from sqlalchemy.orm import Session
from models import AuditLog

def log_action(db: Session, user_id: int, action: str, entity_type: str, entity_id: str, ip_address: str = None):
    """
    Saves an audit log to the database.
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
