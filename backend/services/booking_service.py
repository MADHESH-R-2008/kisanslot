from sqlalchemy.orm import Session
from models import Booking


def generate_booking_id(db: Session) -> str:
    """Generate a unique booking ID like KS1001, KS1002, etc."""
    last_booking = (
        db.query(Booking)
        .order_by(Booking.id.desc())
        .first()
    )

    if last_booking and last_booking.booking_id.startswith("KS"):
        try:
            last_num = int(last_booking.booking_id[2:])
            new_num = last_num + 1
        except ValueError:
            new_num = 1001
    else:
        new_num = 1001

    return f"KS{new_num}"


def generate_token_number(db: Session, slot_id: int) -> int:
    """Generate a sequential token number for a given slot."""
    count = (
        db.query(Booking)
        .filter(Booking.slot_id == slot_id)
        .count()
    )
    return count + 1
