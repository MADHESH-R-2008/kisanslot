from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Centre, Booking, BookingStatusEnum
from schemas import CentreResponse
from auth import get_current_farmer
from services.queue_service import calculate_estimated_wait

router = APIRouter(prefix="/api/centres", tags=["Centres"])


@router.get("", response_model=List[CentreResponse])
def list_centres(db: Session = Depends(get_db)):
    """Return all active procurement centres with live queue count and wait estimate."""
    centres = db.query(Centre).filter(Centre.is_active == True).all()

    result = []
    for c in centres:
        # Count active (non-completed, non-cancelled) bookings for this centre
        queue_count = (
            db.query(Booking)
            .filter(
                Booking.centre_id == c.id,
                Booking.status.notin_([
                    BookingStatusEnum.COMPLETED,
                    BookingStatusEnum.CANCELLED,
                ]),
            )
            .count()
        )

        estimated_wait = calculate_estimated_wait(queue_count, c.active_counters)

        result.append(
            CentreResponse(
                id=c.id,
                name=c.name,
                address=c.address,
                district=c.district,
                state=c.state,
                latitude=c.latitude,
                longitude=c.longitude,
                active_counters=c.active_counters,
                is_active=c.is_active,
                distance_km=c.distance_km,
                rating=c.rating,
                queue_count=queue_count,
                estimated_wait_minutes=estimated_wait,
            )
        )

    return result
