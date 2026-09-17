from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Counter, AdminUser, Centre, Booking, CounterStatusEnum
from schemas import CounterResponse, CounterCreateRequest, CounterUpdateRequest
from auth import get_current_admin
from services.booking_service import format_token_display

router = APIRouter(prefix="/api/counters", tags=["Counters"])


def _build_counter_response(counter, db) -> dict:
    """Build a counter response with current booking info."""
    current_farmer_name = None
    current_token_display = None
    if counter.current_booking_id:
        booking = db.query(Booking).filter(Booking.id == counter.current_booking_id).first()
        if booking:
            current_farmer_name = booking.farmer.name if booking.farmer else None
            current_token_display = format_token_display(booking.centre_id, booking.token_number)

    return CounterResponse(
        id=counter.id,
        centre_id=counter.centre_id,
        name=counter.name,
        status=counter.status.value if hasattr(counter.status, 'value') else counter.status,
        is_available=counter.is_available,
        current_booking_id=counter.current_booking_id,
        current_farmer_name=current_farmer_name,
        current_token_display=current_token_display,
        created_at=counter.created_at,
        updated_at=counter.updated_at,
    )


@router.get("/", response_model=list[CounterResponse])
def list_counters(admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    """List counters for the operator's assigned centre (or all for ADMIN/SUPER_ADMIN)."""
    centre_id = admin.centre_id
    if not centre_id and admin.role.value in ["ADMIN", "SUPER_ADMIN"]:
        # Admin/super can list all counters; optionally filter by query param
        counters = db.query(Counter).filter(Counter.is_deleted == False).all()
    elif centre_id:
        counters = db.query(Counter).filter(Counter.centre_id == centre_id, Counter.is_deleted == False).all()
    else:
        raise HTTPException(status_code=400, detail="Admin not assigned to a centre")

    return [_build_counter_response(c, db) for c in counters]


@router.get("/centre/{centre_id}", response_model=list[CounterResponse])
def list_counters_by_centre(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List counters for a specific centre with authorization check."""
    if admin.role.value == "CENTRE_OPERATOR" and admin.centre_id != centre_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this centre's counters.")

    counters = db.query(Counter).filter(
        Counter.centre_id == centre_id,
        Counter.is_deleted == False,
    ).order_by(Counter.id.asc()).all()

    return [_build_counter_response(c, db) for c in counters]


@router.post("/", response_model=CounterResponse)
def create_counter(req: CounterCreateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    target_centre_id = req.centre_id or admin.centre_id
    if not target_centre_id:
        raise HTTPException(status_code=400, detail="Centre ID is required to create a counter")

    if admin.role.value == "CENTRE_OPERATOR" and admin.centre_id != target_centre_id:
        raise HTTPException(status_code=403, detail="Not authorized to create counter for this centre")

    counter = Counter(
        centre_id=target_centre_id,
        name=req.name,
        status=req.status if req.status else "ACTIVE",
        is_available=req.is_available if req.is_available is not None else True,
    )
    db.add(counter)
    db.commit()
    db.refresh(counter)
    return _build_counter_response(counter, db)


@router.put("/{counter_id}", response_model=CounterResponse)
def update_counter(counter_id: int, req: CounterUpdateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    # Allow ADMIN/SUPER_ADMIN to update any counter
    if admin.role.value in ["ADMIN", "SUPER_ADMIN"]:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.is_deleted == False).first()
    else:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.centre_id == centre_id, Counter.is_deleted == False).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    if req.name is not None:
        counter.name = req.name
    if req.status is not None:
        counter.status = req.status
    if req.is_available is not None:
        counter.is_available = req.is_available
    db.commit()
    db.refresh(counter)
    return _build_counter_response(counter, db)


@router.put("/{counter_id}/toggle")
def toggle_counter(counter_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Toggle counter between ACTIVE and INACTIVE."""
    centre_id = admin.centre_id
    if admin.role.value in ["ADMIN", "SUPER_ADMIN"]:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.is_deleted == False).first()
    else:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.centre_id == centre_id, Counter.is_deleted == False).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")

    current_status = counter.status.value if hasattr(counter.status, 'value') else counter.status
    if current_status == "BUSY":
        raise HTTPException(status_code=409, detail="Cannot toggle a BUSY counter. Complete the current farmer first.")

    if current_status == "ACTIVE":
        counter.status = CounterStatusEnum.INACTIVE
        counter.is_available = False
    else:
        counter.status = CounterStatusEnum.ACTIVE
        counter.is_available = True

    db.commit()
    db.refresh(counter)
    return _build_counter_response(counter, db)


@router.delete("/{counter_id}")
def delete_counter(counter_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = admin.centre_id
    if admin.role.value in ["ADMIN", "SUPER_ADMIN"]:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.is_deleted == False).first()
    else:
        counter = db.query(Counter).filter(Counter.id == counter_id, Counter.centre_id == centre_id, Counter.is_deleted == False).first()

    if not counter:
        raise HTTPException(status_code=404, detail="Counter not found")
    counter.is_deleted = True
    db.commit()
    return {"message": "Counter soft‑deleted"}
