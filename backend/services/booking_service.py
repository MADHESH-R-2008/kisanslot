from datetime import date as date_type
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Booking, Slot


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


def generate_token_number(db: Session, slot_id: int, centre_id: int = None) -> int:
    """
    Generate a sequential, concurrency-safe token number for a given centre and date.
    Uses row/table locking semantics where supported to prevent duplicate tokens.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        return 1

    target_centre_id = centre_id or slot.centre_id

    # Query highest token_number for this centre on this date with row lock if possible
    query = (
        db.query(func.max(Booking.token_number))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(
            Booking.centre_id == target_centre_id,
            Slot.date == slot.date,
        )
    )

    try:
        query = query.with_for_update()
    except Exception:
        pass  # Dialects like SQLite don't support with_for_update

    max_token = query.scalar() or 0
    return max_token + 1


def format_token_display(centre_id: int, token_number: int) -> str:
    """
    Format a token for display.
    Example: centre_id=3, token_number=6 → 'C3-006'
    """
    return f"C{centre_id}-{token_number:03d}"

