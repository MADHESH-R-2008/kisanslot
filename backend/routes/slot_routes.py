from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Slot
from schemas import SlotResponse

router = APIRouter(prefix="/api/centres", tags=["Slots"])


@router.get("/{centre_id}/slots", response_model=List[SlotResponse])
def list_slots(
    centre_id: int,
    date: date = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """Return available slots for a given centre and date."""
    slots = (
        db.query(Slot)
        .filter(
            Slot.centre_id == centre_id,
            Slot.date == date,
        )
        .order_by(Slot.start_time)
        .all()
    )

    result = []
    for s in slots:
        available = max(0, s.capacity - s.booked_count)
        result.append(
            SlotResponse(
                id=s.id,
                start_time=s.start_time.strftime("%H:%M"),
                end_time=s.end_time.strftime("%H:%M"),
                capacity=s.capacity,
                booked_count=s.booked_count,
                available=available,
                is_active=s.is_active and available > 0,
            )
        )

    return result
