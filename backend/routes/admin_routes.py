from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import sqlalchemy as sa
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth import get_current_admin, hash_password, verify_password
from database import get_db
from models import (
    AdminUser, Booking, BookingStatusEnum, Centre, Farmer, Payment,
    Notification, PaymentStatusEnum, Procurement, ProcurementStatusEnum, RoleEnum, Slot,
)

router = APIRouter(prefix="/api/admin", tags=["Administration"])


def _is_system_admin(user: AdminUser) -> bool:
    return user.role in (RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN)


def _require_system_admin(user: AdminUser) -> None:
    if not _is_system_admin(user):
        raise HTTPException(status_code=403, detail="Administrator access required.")


def _scoped_centre(user: AdminUser, requested: Optional[int]) -> Optional[int]:
    if user.role == RoleEnum.CENTRE_OPERATOR:
        if user.centre_id is None:
            raise HTTPException(status_code=403, detail="Operator has no centre assignment.")
        if requested is not None and requested != user.centre_id:
            raise HTTPException(status_code=403, detail="Operator not assigned to this centre.")
        return user.centre_id
    return requested


class OperatorCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    centre_id: int


class OperatorUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class StatusUpdate(BaseModel):
    is_active: bool


class CentreAssignment(BaseModel):
    centre_id: int


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


def _operator_json(operator: AdminUser):
    return {
        "id": operator.id,
        "username": operator.username,
        "role": operator.role.value if hasattr(operator.role, "value") else operator.role,
        "centre_id": operator.centre_id,
        "centre": operator.centre.name if operator.centre else None,
        "is_active": operator.is_active,
        "last_login": operator.last_login,
        "created_at": operator.created_at,
    }


@router.get("/operators")
def list_operators(
    search: Optional[str] = None,
    centre_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _require_system_admin(admin)
    query = db.query(AdminUser).filter(AdminUser.role == RoleEnum.CENTRE_OPERATOR)
    if search:
        query = query.filter(AdminUser.username.ilike(f"%{search.strip()}%"))
    if centre_id is not None:
        query = query.filter(AdminUser.centre_id == centre_id)
    if is_active is not None:
        query = query.filter(AdminUser.is_active == is_active)
    total = query.count()
    items = query.order_by(AdminUser.username).offset((page - 1) * limit).limit(limit).all()
    return {"items": [_operator_json(item) for item in items], "total": total, "page": page, "limit": limit}


@router.get("/operators/{operator_id}")
def get_operator(operator_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_system_admin(admin)
    operator = db.query(AdminUser).filter(AdminUser.id == operator_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found.")
    return _operator_json(operator)


@router.post("/operators", status_code=201)
def create_operator(payload: OperatorCreate, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_system_admin(admin)
    if not db.query(Centre.id).filter(Centre.id == payload.centre_id).first():
        raise HTTPException(status_code=404, detail="Centre not found.")
    if db.query(AdminUser.id).filter(func.lower(AdminUser.username) == payload.username.strip().lower()).first():
        raise HTTPException(status_code=409, detail="Username is already in use.")
    operator = AdminUser(username=payload.username.strip(), password_hash=hash_password(payload.password), role=RoleEnum.CENTRE_OPERATOR, centre_id=payload.centre_id)
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return _operator_json(operator)


@router.put("/operators/{operator_id}")
def update_operator(operator_id: int, payload: OperatorUpdate, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_system_admin(admin)
    operator = db.query(AdminUser).filter(AdminUser.id == operator_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found.")
    if payload.username:
        duplicate = db.query(AdminUser.id).filter(func.lower(AdminUser.username) == payload.username.strip().lower(), AdminUser.id != operator.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Username is already in use.")
        operator.username = payload.username.strip()
    if payload.password:
        operator.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(operator)
    return _operator_json(operator)


@router.put("/operators/{operator_id}/status")
def set_operator_status(operator_id: int, payload: StatusUpdate, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_system_admin(admin)
    operator = db.query(AdminUser).filter(AdminUser.id == operator_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found.")
    operator.is_active = payload.is_active
    db.commit()
    return _operator_json(operator)


@router.put("/operators/{operator_id}/centre")
def assign_operator_centre(operator_id: int, payload: CentreAssignment, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    _require_system_admin(admin)
    operator = db.query(AdminUser).filter(AdminUser.id == operator_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found.")
    if not db.query(Centre.id).filter(Centre.id == payload.centre_id).first():
        raise HTTPException(status_code=404, detail="Centre not found.")
    operator.centre_id = payload.centre_id
    db.commit()
    db.refresh(operator)
    return _operator_json(operator)


@router.get("/farmers")
def list_farmers(search: Optional[str] = None, centre_id: Optional[int] = None, is_active: Optional[bool] = None, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    query = db.query(Farmer)
    if admin.role == RoleEnum.CENTRE_OPERATOR:
        query = query.join(Booking).filter(Booking.centre_id == admin.centre_id).distinct()
    elif centre_id is not None:
        query = query.join(Booking).filter(Booking.centre_id == centre_id).distinct()
    if is_active is not None:
        query = query.filter(Farmer.is_active == is_active)
    if search:
        value = f"%{search.strip()}%"
        query = query.filter(or_(Farmer.name.ilike(value), Farmer.mobile.ilike(value), Farmer.farmer_id.ilike(value)))
    total = query.count()
    farmers = query.order_by(Farmer.name).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": f.id, "name": f.name, "mobile": f.mobile, "farmer_id": f.farmer_id, "village": f.village, "district": f.district, "state": f.state, "is_active": f.is_active, "created_at": f.created_at} for f in farmers], "total": total, "page": page, "limit": limit, "pages": (total + limit - 1) // limit}


@router.get("/farmers/{farmer_id}")
def get_farmer(farmer_id: int, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")
    if admin.role == RoleEnum.CENTRE_OPERATOR and not db.query(Booking.id).filter(Booking.farmer_id == farmer_id, Booking.centre_id == admin.centre_id).first():
        raise HTTPException(status_code=403, detail="Farmer is outside the assigned centre.")
    return {"id": farmer.id, "name": farmer.name, "mobile": farmer.mobile, "farmer_id": farmer.farmer_id, "village": farmer.village, "district": farmer.district, "state": farmer.state, "crop": farmer.crop, "expected_quantity": farmer.expected_quantity, "is_active": farmer.is_active, "created_at": farmer.created_at}


def _farmer_history(db: Session, farmer_id: int, centre_id: Optional[int], page: int, limit: int, date_from: Optional[date], date_to: Optional[date], status_value: Optional[str], history_type: Optional[str]):
    query = db.query(Booking).filter(Booking.farmer_id == farmer_id)
    if centre_id is not None:
        query = query.filter(Booking.centre_id == centre_id)
    if date_from:
        query = query.filter(Booking.booking_date >= date_from)
    if date_to:
        query = query.filter(Booking.booking_date <= date_to)
    if status_value:
        query = query.filter(Booking.status == status_value.upper())
    total = query.count()
    bookings = query.order_by(Booking.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    kind = history_type.upper() if history_type else None
    items = []
    for booking in bookings:
        base = {"booking_id": booking.booking_id, "centre_id": booking.centre_id, "centre": booking.centre.name, "date": booking.booking_date, "token": f"C{booking.centre_id}-{booking.token_number:03d}", "status": booking.status.value, "produce": booking.crop, "quantity": booking.expected_quantity}
        if kind in (None, "BOOKING", "QUEUE"):
            items.append({**base, "type": kind or "BOOKING", "queue": {"called_at": booking.call_time, "serving_started_at": booking.serving_at, "completed_at": booking.completed_at, "counter": booking.assigned_counter}})
        if kind == "PROCUREMENT" and booking.procurement:
            items.append({**base, "type": "PROCUREMENT", "procurement": {"accepted_quantity": booking.procurement.actual_weight, "rejected_quantity": booking.procurement.rejected_quantity, "grade": booking.procurement.quality_status, "rate": booking.procurement.rate, "total_amount": booking.procurement.total_amount, "status": booking.procurement.status.value}})
        if kind == "PAYMENT" and booking.payment:
            items.append({**base, "type": "PAYMENT", "payment": {"amount": booking.payment.amount, "method": booking.payment.payment_method, "transaction_reference": booking.payment.transaction_id, "status": booking.payment.status.value, "payment_date": booking.payment.payment_date}})
    return {"items": items, "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit}


@router.get("/farmers/{farmer_id}/history")
def farmer_history(farmer_id: int, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), date_from: Optional[date] = None, date_to: Optional[date] = None, status: Optional[str] = None, centre_id: Optional[int] = None, history_type: Optional[str] = None, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    scoped = _scoped_centre(admin, centre_id)
    get_farmer(farmer_id, admin, db)
    return _farmer_history(db, farmer_id, scoped, page, limit, date_from, date_to, status, history_type)


@router.get("/payments")
def list_payments(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), status: Optional[str] = None, centre_id: Optional[int] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, farmer_id: Optional[int] = None, search: Optional[str] = None, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = _scoped_centre(admin, centre_id)
    query = db.query(Payment).join(Booking).join(Farmer).join(Centre)
    if centre_id is not None: query = query.filter(Booking.centre_id == centre_id)
    if status: query = query.filter(Payment.status == ("COMPLETED" if status.upper() == "PAID" else status.upper()))
    if date_from: query = query.filter(func.date(Payment.payment_date) >= date_from)
    if date_to: query = query.filter(func.date(Payment.payment_date) <= date_to)
    if farmer_id: query = query.filter(Booking.farmer_id == farmer_id)
    if search:
        value = f"%{search.strip()}%"
        query = query.filter(or_(Payment.transaction_id.ilike(value), Booking.booking_id.ilike(value), Farmer.name.ilike(value)))
    total = query.count()
    rows = query.order_by(Payment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": p.id, "booking_id": p.booking.booking_id, "farmer": p.booking.farmer.name, "farmer_id": p.booking.farmer_id, "centre": p.booking.centre.name, "centre_id": p.booking.centre_id, "amount": p.amount, "payment_method": p.payment_method, "transaction_reference": p.transaction_id, "status": "PAID" if p.status == PaymentStatusEnum.COMPLETED else p.status.value, "payment_date": p.payment_date} for p in rows], "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit}


@router.get("/procurements")
def list_procurements(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), status: Optional[str] = None, centre_id: Optional[int] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, farmer_id: Optional[int] = None, produce_type: Optional[str] = None, search: Optional[str] = None, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = _scoped_centre(admin, centre_id)
    query = db.query(Procurement).join(Booking).join(Farmer).join(Centre)
    if centre_id is not None: query = query.filter(Booking.centre_id == centre_id)
    if status: query = query.filter(Procurement.status == status.upper())
    if date_from: query = query.filter(Booking.booking_date >= date_from)
    if date_to: query = query.filter(Booking.booking_date <= date_to)
    if farmer_id: query = query.filter(Booking.farmer_id == farmer_id)
    if produce_type: query = query.filter(Booking.crop.ilike(f"%{produce_type.strip()}%"))
    if search:
        value = f"%{search.strip()}%"
        query = query.filter(or_(Booking.booking_id.ilike(value), Farmer.name.ilike(value)))
    total = query.count()
    rows = query.order_by(Booking.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"id": p.id, "booking_id": p.booking.booking_id, "token": f"C{p.booking.centre_id}-{p.booking.token_number:03d}", "farmer": p.booking.farmer.name, "farmer_id": p.booking.farmer_id, "centre": p.booking.centre.name, "centre_id": p.booking.centre_id, "produce": p.booking.crop, "quantity": p.booking.expected_quantity, "accepted_quantity": p.actual_weight, "rejected_quantity": p.rejected_quantity, "quality_grade": p.quality_status, "rate": p.rate, "total_amount": p.total_amount, "status": p.status.value, "date": p.procurement_date or p.booking.created_at} for p in rows], "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit}


@router.get("/me")
def admin_profile(admin: AdminUser = Depends(get_current_admin)):
    return _operator_json(admin)


@router.put("/me/password")
def change_password(payload: PasswordChange, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    admin.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully."}


@router.get("/bookings")
def list_bookings(search: Optional[str] = None, centre_id: Optional[int] = None, status: Optional[str] = None, booking_date: Optional[date] = None, produce: Optional[str] = None, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=100), admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    centre_id = _scoped_centre(admin, centre_id)
    query = db.query(Booking).join(Farmer).join(Centre).join(Slot)
    if centre_id is not None:
        query = query.filter(Booking.centre_id == centre_id)
    if status:
        query = query.filter(Booking.status == status.upper())
    if booking_date:
        query = query.filter(Booking.booking_date == booking_date)
    if produce:
        query = query.filter(Booking.crop.ilike(f"%{produce.strip()}%"))
    if search:
        value = f"%{search.strip()}%"
        query = query.filter(or_(Booking.booking_id.ilike(value), Farmer.name.ilike(value)))
    total = query.count()
    rows = query.order_by(Booking.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [{"booking_id": b.booking_id, "farmer": b.farmer.name, "centre": b.centre.name, "centre_id": b.centre_id, "date": b.booking_date, "slot": f"{b.slot.start_time:%H:%M}-{b.slot.end_time:%H:%M}", "token": f"C{b.centre_id}-{b.token_number:03d}", "produce": b.crop, "quantity": b.expected_quantity, "status": b.status.value, "created_at": b.created_at} for b in rows], "total": total, "page": page, "limit": limit}


def _analytics(admin: AdminUser, db: Session, requested_centre: Optional[int]):
    centre_id = _scoped_centre(admin, requested_centre)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    bookings = db.query(Booking)
    procurements = db.query(Procurement).join(Booking)
    payments = db.query(Payment).join(Booking)
    if centre_id is not None:
        bookings = bookings.filter(Booking.centre_id == centre_id)
        procurements = procurements.filter(Booking.centre_id == centre_id)
        payments = payments.filter(Booking.centre_id == centre_id)
    dialect = db.get_bind().dialect.name
    completed_waits = bookings.filter(Booking.call_time.isnot(None), Booking.arrival_time.isnot(None))
    if dialect == "postgresql":
        average_wait = completed_waits.with_entities(func.avg(func.extract("epoch", Booking.call_time - Booking.arrival_time) / 60)).scalar()
    elif dialect == "mysql":
        average_wait = completed_waits.with_entities(func.avg(func.timestampdiff(sa.text("MINUTE"), Booking.arrival_time, Booking.call_time))).scalar()
    else:
        average_wait = completed_waits.with_entities(func.avg((func.julianday(Booking.call_time) - func.julianday(Booking.arrival_time)) * 1440)).scalar()
    return {
        "centre_id": centre_id,
        "bookings": {"today": bookings.filter(Booking.booking_date == today).count(), "week": bookings.filter(Booking.booking_date >= week_start).count(), "month": bookings.filter(Booking.booking_date >= month_start).count()},
        "queue": {"waiting": bookings.filter(Booking.status.in_([BookingStatusEnum.CONFIRMED, BookingStatusEnum.WAITING, BookingStatusEnum.CALLED])).count(), "completed": bookings.filter(Booking.status == BookingStatusEnum.COMPLETED).count(), "average_wait_minutes": round(float(average_wait or 0), 1)},
        "procurement": {"total_quantity": float(procurements.with_entities(func.coalesce(func.sum(Procurement.actual_weight), 0)).scalar() or 0), "completed": procurements.filter(Procurement.status == ProcurementStatusEnum.COMPLETED).count(), "pending": procurements.filter(Procurement.status != ProcurementStatusEnum.COMPLETED).count()},
        "payments": {"pending": payments.filter(Payment.status == PaymentStatusEnum.PENDING).count(), "processing": payments.filter(Payment.status == PaymentStatusEnum.PROCESSING).count(), "paid": payments.filter(Payment.status == PaymentStatusEnum.COMPLETED).count(), "failed": payments.filter(Payment.status == PaymentStatusEnum.FAILED).count(), "total_paid_amount": float(payments.filter(Payment.status == PaymentStatusEnum.COMPLETED).with_entities(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0)},
    }


@router.get("/analytics/overview")
@router.get("/analytics/bookings")
@router.get("/analytics/queue")
@router.get("/analytics/procurement")
@router.get("/analytics/payments")
def analytics(centre_id: Optional[int] = None, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    return _analytics(admin, db, centre_id)
