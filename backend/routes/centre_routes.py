from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import hash_password
from database import get_db
from dependencies import enforce_operator_centre, get_current_admin, require_admin_or_super
from models import AdminUser, Booking, Centre, Counter, Payment, Procurement, RoleEnum, Slot
from schemas import CentreCreateRequest, CentreResponse, CentreUpdateRequest

router = APIRouter(prefix="/api/centres", tags=["Centres"])


import math

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


@router.get("", response_model=List[CentreResponse])
@router.get("/", response_model=List[CentreResponse])
def list_centres(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """List active and inactive centres with dynamic real distance calculation."""
    try:
        centres = db.query(Centre).all()
        if not centres:
            try:
                from seed import _ensure_centres
                centres = _ensure_centres(db)
            except Exception:
                centres = db.query(Centre).all()
        res = []
        for c in centres:
            try:
                today = date.today()
                q_count = (
                    db.query(Booking)
                    .join(Slot, Booking.slot_id == Slot.id)
                    .filter(
                        Booking.centre_id == c.id,
                        Slot.date == today,
                        Booking.status.in_(["WAITING", "CALLED", "SERVING", "CONFIRMED"]),
                    )
                    .count()
                )
            except Exception:
                q_count = 0

            calc_dist = getattr(c, "distance_km", 0.0) or 0.0
            c_lat = getattr(c, "latitude", None)
            c_lon = getattr(c, "longitude", None)
            if lat is not None and lon is not None and c_lat and c_lon:
                computed = haversine_km(lat, lon, c_lat, c_lon)
                if computed > 0:
                    calc_dist = computed

            c_dict = {
                "id": c.id,
                "name": c.name,
                "code": c.code,
                "address": c.address or "",
                "district": c.district or "",
                "state": c.state or "",
                "contact_number": getattr(c, "contact_number", None),
                "latitude": c_lat or 0.0,
                "longitude": c_lon or 0.0,
                "total_counters": getattr(c, "total_counters", 3) or 3,
                "active_counters": getattr(c, "active_counters", 3) or 3,
                "is_active": getattr(c, "is_active", True) if getattr(c, "is_active", True) is not None else True,
                "is_paused": getattr(c, "is_paused", False) if getattr(c, "is_paused", False) is not None else False,
                "distance_km": calc_dist,
                "rating": getattr(c, "rating", 4.5) or 4.5,
                "google_map_url": getattr(c, "google_map_url", None),
                "queue_count": q_count,
                "estimated_wait_minutes": q_count * 6,
            }
            res.append(c_dict)
        return res
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Centre list error: {str(e)} | Trace: {traceback.format_exc()}")


@router.post("", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(
    payload: CentreCreateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin or Master: create a centre and its Centre ID/password operator login."""
    if admin.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin or Master account required to create centres")

    clean_code = payload.code.strip()
    centre = Centre(
        name=payload.name.strip(),
        code=clean_code,
        address=payload.address.strip() if payload.address else "",
        district=payload.district.strip() if payload.district else "",
        state=payload.state.strip() if payload.state else "",
        latitude=payload.latitude,
        longitude=payload.longitude,
        contact_number=payload.contact_number,
        total_counters=payload.total_counters,
        active_counters=payload.active_counters,
        is_active=payload.is_active,
        is_paused=payload.is_paused,
        distance_km=payload.distance_km,
        rating=payload.rating,
        google_map_url=payload.google_map_url,
    )
    db.add(centre)
    try:
        db.flush()
        db.add(AdminUser(
            username=clean_code,
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

    update_data = payload.dict(exclude_unset=True)
    operator_password = update_data.pop("operator_password", None)

    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip()

    for attr, value in update_data.items():
        setattr(centre, attr, value)

    # Sync associated AdminUser operator credentials
    admin_user = db.query(AdminUser).filter(AdminUser.centre_id == centre.id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not admin_user:
        admin_user = db.query(AdminUser).filter(AdminUser.username == centre.code).first()

    if "code" in update_data and update_data["code"]:
        if admin_user:
            admin_user.username = update_data["code"]
        else:
            admin_user = AdminUser(
                username=update_data["code"],
                password_hash=hash_password(operator_password or "op123456"),
                role=RoleEnum.CENTRE_OPERATOR,
                centre_id=centre.id,
            )
            db.add(admin_user)

    if operator_password and operator_password.strip():
        if admin_user:
            admin_user.password_hash = hash_password(operator_password.strip())
        else:
            admin_user = AdminUser(
                username=centre.code,
                password_hash=hash_password(operator_password.strip()),
                role=RoleEnum.CENTRE_OPERATOR,
                centre_id=centre.id,
            )
            db.add(admin_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That Centre ID is already in use")
    db.refresh(centre)
    return centre


@router.delete("", status_code=status.HTTP_200_OK)
@router.delete("/", status_code=status.HTTP_200_OK)
def delete_all_centres(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Master-only destructive reset of all centres and their centre-owned data."""
    if admin.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin or Master account required to delete centres")

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
    """Admin or Master deletion for a specific centre and all its associated data."""
    if admin.role not in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Admin or Master account required to delete centres")

    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")

    booking_ids = [b_id for (b_id,) in db.query(Booking.id).filter(Booking.centre_id == centre_id).all()]
    try:
        # FK-safe cascade delete for single centre
        db.query(Counter).filter(Counter.centre_id == centre_id).delete(synchronize_session=False)
        if booking_ids:
            db.query(Payment).filter(Payment.booking_id.in_(booking_ids)).delete(synchronize_session=False)
            db.query(Procurement).filter(Procurement.booking_id.in_(booking_ids)).delete(synchronize_session=False)
            db.query(Booking).filter(Booking.centre_id == centre_id).delete(synchronize_session=False)
        db.query(Slot).filter(Slot.centre_id == centre_id).delete(synchronize_session=False)
        db.query(AdminUser).filter(AdminUser.centre_id == centre_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).delete(synchronize_session=False)
        db.query(AdminUser).filter(AdminUser.centre_id == centre_id).update({AdminUser.centre_id: None}, synchronize_session=False)

        db.delete(centre)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete centre: {str(e)}")

    return {"message": "Centre and all associated data deleted successfully"}
