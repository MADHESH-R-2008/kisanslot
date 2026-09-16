from datetime import date as date_type
from sqlalchemy.orm import Session
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
    Generate a sequential token number for a given centre and date.
    Phase 3.2: Tokens are now per-centre-per-date (not per-slot).
    Falls back to per-slot if centre_id not provided (backward compat).
    """
    if centre_id is not None:
        # Get the slot date
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if slot:
            # Count all bookings for this centre on the same date
            count = (
                db.query(Booking)
                .join(Slot, Booking.slot_id == Slot.id)
                .filter(
                    Booking.centre_id == centre_id,
                    Slot.date == slot.date,
                )
                .count()
            )
            return count + 1

    # Fallback: per-slot token (backward compat)
    count = (
        db.query(Booking)
        .filter(Booking.slot_id == slot_id)
        .count()
    )
    return count + 1


def format_token_display(centre_id: int, token_number: int) -> str:
    """
    Format a token for display.
    Example: centre_id=3, token_number=15 → 'C003-015'
    """
    return f"C{centre_id:03d}-{token_number:03d}"
