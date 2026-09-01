from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Centre, BookingStatusEnum
from schemas import QueueResponse
from auth import get_current_farmer
from services.queue_service import calculate_queue_position

router = APIRouter(prefix="/api/queue", tags=["Queue"])


@router.get("/{booking_id}", response_model=QueueResponse)
def get_queue_position(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Calculate live queue position for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    if booking.farmer_id != farmer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this queue.",
        )

    centre = db.query(Centre).filter(Centre.id == booking.centre_id).first()
    active_counters = centre.active_counters if centre else 3

    queue_data = calculate_queue_position(db, booking, active_counters)

    return QueueResponse(
        booking_id=booking.booking_id,
        queue_position=queue_data["queue_position"],
        farmers_ahead=queue_data["farmers_ahead"],
        estimated_wait_minutes=queue_data["estimated_wait_minutes"],
        active_counters=active_counters,
        status=queue_data["status"],
    )
