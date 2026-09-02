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

@router.post("/rollover", tags=["Admin"])
def rollover_slots(db: Session = Depends(get_db)):
    """Close slots for past dates and open slots for the next 7 days for all active centres."""
    from datetime import date, timedelta, time
    from models import Centre
    
    try:
        today = date.today()
        
        # 1. Close past slots
        closed_count = (
            db.query(Slot)
            .filter(Slot.date < today, Slot.is_active == True)
            .update({Slot.is_active: False}, synchronize_session="fetch")
        )
            
        # 2. Open slots for next 7 days for all active centres
        active_centres = db.query(Centre).filter(Centre.is_active == True).all()
        
        slot_times = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
        ]
        
        new_slots_count = 0
        for centre in active_centres:
            for i in range(7):
                target_date = today + timedelta(days=i)
                # Check if slots already exist for this date and centre
                existing = db.query(Slot).filter(
                    Slot.centre_id == centre.id, 
                    Slot.date == target_date
                ).first()
                if not existing:
                    for start, end in slot_times:
                        slot = Slot(
                            centre_id=centre.id,
                            date=target_date,
                            start_time=start,
                            end_time=end,
                            capacity=25,
                            booked_count=0,
                            is_active=True,
                        )
                        db.add(slot)
                        new_slots_count += 1
                        
        db.commit()
        return {
            "message": "Rollover complete",
            "today": str(today),
            "closed_slots": closed_count,
            "new_slots": new_slots_count,
            "centres": len(active_centres),
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "type": type(e).__name__}

