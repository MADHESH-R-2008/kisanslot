import math
from sqlalchemy.orm import Session
from models import Booking, BookingStatusEnum, Counter, CounterStatusEnum
from config import get_settings

settings = get_settings()

# Statuses considered "active" in the queue (not yet done)
ACTIVE_QUEUE_STATUSES = [
    BookingStatusEnum.CONFIRMED,
    BookingStatusEnum.ARRIVED,
    BookingStatusEnum.VERIFIED,
    BookingStatusEnum.WAITING,
    BookingStatusEnum.CALLED,
    BookingStatusEnum.SERVING,
    BookingStatusEnum.PROCESSING,
]

# Statuses considered "waiting" (eligible to be called)
WAITING_STATUSES = [
    BookingStatusEnum.CONFIRMED,
    BookingStatusEnum.ARRIVED,
    BookingStatusEnum.VERIFIED,
    BookingStatusEnum.WAITING,
]

# Statuses that are terminal (no longer in queue)
TERMINAL_STATUSES = [
    BookingStatusEnum.COMPLETED,
    BookingStatusEnum.CANCELLED,
    BookingStatusEnum.NO_SHOW,
    BookingStatusEnum.SKIPPED,
]


def get_active_counter_count(db: Session, centre_id: int) -> int:
    """Get the number of active (ACTIVE or BUSY) counters for a centre."""
    count = (
        db.query(Counter)
        .filter(
            Counter.centre_id == centre_id,
            Counter.is_deleted == False,
            Counter.status.in_([CounterStatusEnum.ACTIVE, CounterStatusEnum.BUSY]),
        )
        .count()
    )
    return max(count, 1)  # Never return 0 to avoid division by zero


def get_available_counter(db: Session, centre_id: int):
    """Find the first available (ACTIVE, not BUSY) counter for a centre."""
    return (
        db.query(Counter)
        .filter(
            Counter.centre_id == centre_id,
            Counter.is_deleted == False,
            Counter.status == CounterStatusEnum.ACTIVE,
            Counter.is_available == True,
        )
        .order_by(Counter.id.asc())
        .first()
    )


def calculate_estimated_wait(farmers_ahead: int, active_counters: int) -> int:
    """
    Calculate estimated wait time in minutes.
    Formula: farmers_ahead × average_processing_time ÷ active_counters
    """
    if active_counters <= 0:
        active_counters = 1

    avg_time = settings.AVERAGE_PROCESSING_TIME_MINUTES
    wait = (farmers_ahead * avg_time) / active_counters
    return math.ceil(wait)


def calculate_queue_position(db: Session, booking: Booking, active_counters: int = None) -> dict:
    """
    Calculate the queue position for a specific booking.
    Phase 3.2: Position is based on same centre, same date, earlier token_number,
    and only counts bookings in waiting statuses.
    """
    # Use real counter count if not provided
    if active_counters is None:
        active_counters = get_active_counter_count(db, booking.centre_id)

    # If booking is already completed, cancelled, skipped, or no_show
    status_val = booking.status.value if hasattr(booking.status, 'value') else booking.status
    if status_val in [s.value for s in TERMINAL_STATUSES]:
        return {
            "queue_position": 0,
            "farmers_ahead": 0,
            "estimated_wait_minutes": 0,
            "status": status_val,
            "assigned_counter": booking.assigned_counter,
        }

    # If currently being served or called
    if status_val in [BookingStatusEnum.CALLED.value, BookingStatusEnum.SERVING.value, BookingStatusEnum.PROCESSING.value]:
        return {
            "queue_position": 0,
            "farmers_ahead": 0,
            "estimated_wait_minutes": 0,
            "status": status_val,
            "assigned_counter": booking.assigned_counter,
        }

    # Count farmers ahead: same centre, same slot date, waiting statuses,
    # with a lower token_number (earlier in queue)
    from models import Slot
    slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
    slot_date = slot.date if slot else None

    if slot_date:
        farmers_ahead = (
            db.query(Booking)
            .join(Slot, Booking.slot_id == Slot.id)
            .filter(
                Booking.centre_id == booking.centre_id,
                Slot.date == slot_date,
                Booking.token_number < booking.token_number,
                Booking.status.in_(WAITING_STATUSES),
            )
            .count()
        )
    else:
        # Fallback to slot-level if no date
        farmers_ahead = (
            db.query(Booking)
            .filter(
                Booking.slot_id == booking.slot_id,
                Booking.id < booking.id,
                Booking.status.notin_(TERMINAL_STATUSES),
            )
            .count()
        )

    queue_position = farmers_ahead + 1
    estimated_wait = calculate_estimated_wait(farmers_ahead, active_counters)

    return {
        "queue_position": queue_position,
        "farmers_ahead": farmers_ahead,
        "estimated_wait_minutes": estimated_wait,
        "status": status_val,
        "assigned_counter": booking.assigned_counter,
    }
