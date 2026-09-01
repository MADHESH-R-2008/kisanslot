import math
from sqlalchemy.orm import Session
from models import Booking, BookingStatusEnum
from config import get_settings

settings = get_settings()


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


def calculate_queue_position(db: Session, booking: Booking, active_counters: int) -> dict:
    """
    Calculate the queue position for a specific booking.
    Position is based on bookings in the same slot that were created
    before this booking and are still active (not completed/cancelled).
    """
    # If booking is already completed or cancelled
    if booking.status in [BookingStatusEnum.COMPLETED, BookingStatusEnum.CANCELLED]:
        return {
            "queue_position": 0,
            "farmers_ahead": 0,
            "estimated_wait_minutes": 0,
            "status": booking.status.value,
        }

    # Count bookings in the same slot that were created before this one
    # and are still active
    farmers_ahead = (
        db.query(Booking)
        .filter(
            Booking.slot_id == booking.slot_id,
            Booking.id < booking.id,
            Booking.status.notin_([
                BookingStatusEnum.COMPLETED,
                BookingStatusEnum.CANCELLED,
            ]),
        )
        .count()
    )

    queue_position = farmers_ahead + 1
    estimated_wait = calculate_estimated_wait(farmers_ahead, active_counters)

    # Determine display status
    if farmers_ahead == 0:
        display_status = "YOUR_TURN"
    elif farmers_ahead <= 2:
        display_status = "ALMOST"
    else:
        display_status = "WAITING"

    return {
        "queue_position": queue_position,
        "farmers_ahead": farmers_ahead,
        "estimated_wait_minutes": estimated_wait,
        "status": display_status,
    }
