from datetime import date, time, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Slot, Centre, AdminUser, RoleEnum
from schemas import SlotResponse, SlotCreateRequest, SlotUpdateRequest
from auth import get_current_admin

router = APIRouter(prefix="/api", tags=["Slots"])


def _parse_time(t_str: str) -> time:
    """Parse time string like '09:00' or '09:00:00' into datetime.time."""
    parts = t_str.split(":")
    if len(parts) >= 2:
        return time(int(parts[0]), int(parts[1]))
    raise ValueError(f"Invalid time format: {t_str}")


def _build_slot_response(s: Slot) -> SlotResponse:
    available = max(0, s.capacity - s.booked_count)
    if not s.is_active:
        slot_status = "CLOSED"
    elif available <= 0:
        slot_status = "FULL"
    else:
        slot_status = "AVAILABLE"

    return SlotResponse(
        id=s.id,
        centre_id=s.centre_id,
        date=s.date,
        start_time=s.start_time.strftime("%H:%M"),
        end_time=s.end_time.strftime("%H:%M"),
        capacity=s.capacity,
        maximum_capacity=s.capacity,
        booked_count=s.booked_count,
        available=available,
        status=slot_status,
        is_active=s.is_active and available > 0,
    )


@router.get("/centres/{centre_id}/slots", response_model=List[SlotResponse])
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

    return [_build_slot_response(s) for s in slots]


@router.post("/slots", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(
    req: SlotCreateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new slot (Admin / Operator for assigned centre)."""
    if admin.role == RoleEnum.CENTRE_OPERATOR and admin.centre_id != req.centre_id:
        raise HTTPException(status_code=403, detail="You are not authorized for this centre.")

    centre = db.query(Centre).filter(Centre.id == req.centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found.")
    if not centre.is_active:
        raise HTTPException(status_code=400, detail="Cannot create slots for inactive centre.")

    try:
        start_t = _parse_time(req.start_time)
        end_t = _parse_time(req.end_time)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    cap = req.maximum_capacity or req.capacity or 25
    if cap <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be greater than 0.")

    existing = db.query(Slot).filter(
        Slot.centre_id == req.centre_id,
        Slot.date == req.date,
        Slot.start_time == start_t,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="A slot already exists at this start time.")

    slot = Slot(
        centre_id=req.centre_id,
        date=req.date,
        start_time=start_t,
        end_time=end_t,
        capacity=cap,
        booked_count=0,
        is_active=req.is_active if req.is_active is not None else True,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return _build_slot_response(slot)


@router.put("/slots/{slot_id}", response_model=SlotResponse)
def update_slot(
    slot_id: int,
    req: SlotUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update slot details (capacity, active state, status)."""
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found.")

    if admin.role == RoleEnum.CENTRE_OPERATOR and admin.centre_id != slot.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized for this centre.")

    new_cap = req.maximum_capacity or req.capacity
    if new_cap is not None:
        if new_cap < slot.booked_count:
            raise HTTPException(
                status_code=400,
                detail=f"Capacity cannot be less than booked count ({slot.booked_count}).",
            )
        slot.capacity = new_cap

    if req.is_active is not None:
        slot.is_active = req.is_active

    if req.status is not None:
        if req.status in ["CLOSED", "CANCELLED"]:
            slot.is_active = False
        elif req.status in ["AVAILABLE"]:
            slot.is_active = True

    if req.start_time:
        try:
            slot.start_time = _parse_time(req.start_time)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    if req.end_time:
        try:
            slot.end_time = _parse_time(req.end_time)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    db.commit()
    db.refresh(slot)
    return _build_slot_response(slot)


@router.delete("/slots/{slot_id}")
def delete_slot(
    slot_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Deactivate/delete a slot."""
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found.")

    if admin.role == RoleEnum.CENTRE_OPERATOR and admin.centre_id != slot.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized for this centre.")

    slot.is_active = False
    db.commit()
    return {"message": "Slot deactivated", "slot_id": slot_id}


@router.post("/centres/rollover", tags=["Admin"])
def rollover_slots(db: Session = Depends(get_db)):
    """Close slots for past dates and open slots for the next 7 days for all active centres."""
    from datetime import date, timedelta, time
    import traceback

    try:
        today = date.today()

        # 1. Close past slots
        past_slots = db.query(Slot).filter(Slot.date < today, Slot.is_active == True).all()
        for s in past_slots:
            s.is_active = False

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
            "closed_slots": len(past_slots),
            "new_slots": new_slots_count,
            "centres": len(active_centres),
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e), "type": type(e).__name__, "traceback": traceback.format_exc()}

