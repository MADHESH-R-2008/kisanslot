from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import hash_password
from database import get_db
from dependencies import enforce_operator_centre, get_current_admin, require_admin_or_super
from models import AdminUser, Booking, Centre, Counter, Payment, Procurement, RoleEnum, Slot
from schemas import CentreCreateRequest, CentreResponse, CentreUpdateRequest

router = APIRouter(prefix="/api/centres", tags=["Centres"])


@router.get("", response_model=List[CentreResponse])
@router.get("/", response_model=List[CentreResponse])
def list_centres(db: Session = Depends(get_db)):
    """List active and inactive centres for the app and dashboard."""
    return db.query(Centre).all()


@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(
    payload: CentreCreateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Master-only: create a centre and its Centre ID/password operator login."""
    if admin.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only the Master can create centres")

    centre = Centre(
        name=payload.name,
        code=payload.code,
        address=payload.address,
        district=payload.district,
        state=payload.state,
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_number=payload.contact_number,
        total_counters=payload.total_counters,
        active_counters=payload.active_counters,
        is_active=payload.is_active,
        is_paused=payload.is_paused,
        distance_km=payload.distance_km,
        rating=payload.rating,
    )
    db.add(centre)
    try:
        db.flush()
        db.add(AdminUser(
            username=payload.code,
            password_hash=hash_password(payload.operator_password),
            role=RoleEnum.CENTRE_OPERATOR,
            centre_id=centre.id,
        ))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That Centre ID is already in use")

    db.refresh(centre)
    return centre


@router.put("/{centre_id}", response_model=CentreResponse)
def update_centre(
    centre_id: int,
    payload: CentreUpdateRequest,
    admin: dict = Depends(require_admin_or_super()),
    db: Session = Depends(get_db),
    _: bool = Depends(enforce_operator_centre),
):
    """Masters/Admins can update all centres; operators can update their own."""
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(centre, attr, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That Centre ID is already in use")
    db.refresh(centre)
    return centre


@router.delete("/", status_code=status.HTTP_200_OK)
def delete_all_centres(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Master-only destructive reset of all centres and their centre-owned data."""
    if admin.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only the Master can delete all centres")

    centre_ids = [centre_id for (centre_id,) in db.query(Centre.id).all()]
    if not centre_ids:
        return {"message": "No centres to delete", "deleted_centres": 0}

    booking_ids = [booking_id for (booking_id,) in db.query(Booking.id).filter(Booking.centre_id.in_(centre_ids)).all()]
    try:
        # Remove dependants in foreign-key-safe order.
        db.query(Counter).filter(Counter.centre_id.in_(centre_ids)).delete(synchronize_session=False)
        if booking_ids:
            db.query(Payment).filter(Payment.booking_id.in_(booking_ids)).delete(synchronize_session=False)
            db.query(Procurement).filter(Procurement.booking_id.in_(booking_ids)).delete(synchronize_session=False)
            db.query(Booking).filter(Booking.id.in_(booking_ids)).delete(synchronize_session=False)
        db.query(Slot).filter(Slot.centre_id.in_(centre_ids)).delete(synchronize_session=False)
        db.query(AdminUser).filter(
            AdminUser.centre_id.in_(centre_ids),
            AdminUser.role == RoleEnum.CENTRE_OPERATOR,
        ).delete(synchronize_session=False)
        db.query(AdminUser).filter(AdminUser.centre_id.in_(centre_ids)).update(
            {AdminUser.centre_id: None}, synchronize_session=False,
        )
        deleted_centres = db.query(Centre).filter(Centre.id.in_(centre_ids)).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not delete all centres")

    return {"message": "All centres and their operator accounts were deleted", "deleted_centres": deleted_centres}


@router.delete("/{centre_id}")
def delete_centre(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Master-only deletion for centres that do not have booking history."""
    if admin.role != RoleEnum.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only the Master can delete centres")

    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    if centre.bookings:
        raise HTTPException(
            status_code=409,
            detail="This centre has booking history. Use Delete all centres to reset centre data.",
        )
    db.delete(centre)
    db.commit()
    return {"message": "Centre deleted"}
