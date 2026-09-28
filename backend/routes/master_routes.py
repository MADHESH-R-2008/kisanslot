from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_admin, hash_password
from database import get_db
from models import (
    AdminUser, AuditLog, Booking, BookingStatusEnum, Centre, Counter, District,
    MasterProfile, OperatorProfile, Payment, PaymentStatusEnum, Procurement,
    ProcurementStatusEnum, RoleEnum, Slot,
)

master_router = APIRouter(prefix="/api/master", tags=["Master"])
super_router = APIRouter(prefix="/api/super-admin", tags=["Super Admin"])


class CentrePayload(BaseModel):
    name: str
    code: str
    address: str
    contact_number: Optional[str] = None
    latitude: float = 0
    longitude: float = 0
    total_counters: int = Field(3, ge=1)
    is_active: bool = True


class CentreUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    contact_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_counters: Optional[int] = Field(None, ge=1)


class StatusPayload(BaseModel):
    is_active: bool


class OperatorPayload(BaseModel):
    full_name: str
    username: str
    mobile: Optional[str] = None
    password: str = Field(min_length=8)
    centre_id: int
    is_active: bool = True


class OperatorUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    mobile: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class CentreAssignment(BaseModel):
    centre_id: int


class MasterPayload(BaseModel):
    full_name: str
    username: str
    mobile: Optional[str] = None
    password: str = Field(min_length=8)
    district_id: int
    is_active: bool = True


class MasterUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    district_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=8)


def _role(user: AdminUser) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def _master(user: AdminUser = Depends(get_current_admin)) -> AdminUser:
    if _role(user) != RoleEnum.MASTER.value or not user.district_id:
        raise HTTPException(403, "MASTER access with an assigned district is required")
    return user


def _super(user: AdminUser = Depends(get_current_admin)) -> AdminUser:
    if _role(user) != RoleEnum.SUPER_ADMIN.value:
        raise HTTPException(403, "SUPER_ADMIN access required")
    return user


def _centre_for_master(db: Session, master: AdminUser, centre_id: int) -> Centre:
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(404, "Centre not found")
    if centre.district_id != master.district_id:
        raise HTTPException(403, "Centre belongs to another district")
    return centre


def _audit(db: Session, user: AdminUser, action: str, entity: str, entity_id) -> None:
    db.add(AuditLog(user_id=str(user.id), role=_role(user), action=action, entity_type=entity,
                    entity_id=str(entity_id), district_id=user.district_id))


def _centre_dict(centre: Centre, db: Session) -> dict:
    today = date.today()
    return {
        "id": centre.id, "name": centre.name, "code": centre.code,
        "district_id": centre.district_id, "district": centre.district_ref.name if centre.district_ref else centre.district,
        "address": centre.address, "contact_number": centre.contact_number,
        "latitude": centre.latitude, "longitude": centre.longitude,
        "is_active": centre.is_active, "total_counters": centre.total_counters,
        "active_counters": db.query(Counter).filter(Counter.centre_id == centre.id, Counter.is_available.is_(True), Counter.is_deleted.is_(False)).count(),
        "today_bookings": db.query(Booking).filter(Booking.centre_id == centre.id, Booking.booking_date == today, Booking.is_deleted.is_(False)).count(),
        "queue": db.query(Booking).filter(Booking.centre_id == centre.id, Booking.booking_date == today, Booking.status.in_([BookingStatusEnum.WAITING, BookingStatusEnum.CALLED, BookingStatusEnum.SERVING])).count(),
        "operators": db.query(AdminUser).filter(AdminUser.centre_id == centre.id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).count(),
    }


@master_router.get("/profile")
def master_profile(master: AdminUser = Depends(_master)):
    return {"id": master.id, "full_name": master.full_name, "username": master.username, "mobile": master.mobile,
            "role": _role(master), "district_id": master.district_id, "district": master.district.name}


@master_router.get("/district")
def master_district(master: AdminUser = Depends(_master)):
    return {"id": master.district.id, "name": master.district.name, "code": master.district.code,
            "state": master.district.state, "status": master.district.status}


@master_router.get("/dashboard")
def dashboard(master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    centre_ids = [row[0] for row in db.query(Centre.id).filter(Centre.district_id == master.district_id).all()]
    bookings = db.query(Booking).filter(Booking.centre_id.in_(centre_ids), Booking.booking_date == date.today()) if centre_ids else db.query(Booking).filter(False)
    return {
        "district": master.district.name,
        "total_centres": db.query(Centre).filter(Centre.district_id == master.district_id).count(),
        "active_centres": db.query(Centre).filter(Centre.district_id == master.district_id, Centre.is_active.is_(True)).count(),
        "inactive_centres": db.query(Centre).filter(Centre.district_id == master.district_id, Centre.is_active.is_(False)).count(),
        "total_operators": db.query(AdminUser).filter(AdminUser.centre_id.in_(centre_ids), AdminUser.role == RoleEnum.CENTRE_OPERATOR).count() if centre_ids else 0,
        "today_bookings": bookings.count(),
        "live_queue": bookings.filter(Booking.status.in_([BookingStatusEnum.WAITING, BookingStatusEnum.CALLED, BookingStatusEnum.SERVING])).count(),
        "pending_procurement": db.query(Procurement).join(Booking).filter(Booking.centre_id.in_(centre_ids), Procurement.status != ProcurementStatusEnum.COMPLETED).count() if centre_ids else 0,
        "pending_payments": db.query(Payment).join(Booking).filter(Booking.centre_id.in_(centre_ids), Payment.status != PaymentStatusEnum.COMPLETED).count() if centre_ids else 0,
    }


@master_router.get("/centres")
def list_centres(search: Optional[str] = None, is_active: Optional[bool] = None, page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    query = db.query(Centre).filter(Centre.district_id == master.district_id)
    if search: query = query.filter(Centre.name.ilike(f"%{search.strip()}%") | Centre.code.ilike(f"%{search.strip()}%"))
    if is_active is not None: query = query.filter(Centre.is_active == is_active)
    total = query.count(); rows = query.order_by(Centre.name).offset((page - 1) * limit).limit(limit).all()
    return {"items": [_centre_dict(c, db) for c in rows], "total": total, "page": page, "limit": limit}


@master_router.post("/centres", status_code=201)
def create_centre(payload: CentrePayload, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    if db.query(Centre.id).filter(Centre.code == payload.code.strip()).first(): raise HTTPException(409, "Centre code already exists")
    centre = Centre(**payload.model_dump(), district_id=master.district_id, district=master.district.name, state=master.district.state, active_counters=0)
    db.add(centre); db.flush(); _audit(db, master, "CREATE_CENTRE", "CENTRE", centre.id); db.commit(); db.refresh(centre)
    return _centre_dict(centre, db)


@master_router.get("/centres/{centre_id}")
def centre_detail(centre_id: int, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    centre = _centre_for_master(db, master, centre_id); data = _centre_dict(centre, db)
    data.update({"available_slots": db.query(Slot).filter(Slot.centre_id == centre.id, Slot.date >= date.today(), Slot.is_active.is_(True)).count(),
                 "pending_procurement": db.query(Procurement).join(Booking).filter(Booking.centre_id == centre.id, Procurement.status != ProcurementStatusEnum.COMPLETED).count(),
                 "pending_payments": db.query(Payment).join(Booking).filter(Booking.centre_id == centre.id, Payment.status != PaymentStatusEnum.COMPLETED).count()})
    return data


@master_router.put("/centres/{centre_id}")
def update_centre(centre_id: int, payload: CentreUpdate, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    centre = _centre_for_master(db, master, centre_id)
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(centre, key, value)
    _audit(db, master, "UPDATE_CENTRE", "CENTRE", centre.id); db.commit(); return _centre_dict(centre, db)


@master_router.put("/centres/{centre_id}/status")
def centre_status(centre_id: int, payload: StatusPayload, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    centre = _centre_for_master(db, master, centre_id); centre.is_active = payload.is_active
    _audit(db, master, "ACTIVATE_CENTRE" if payload.is_active else "DEACTIVATE_CENTRE", "CENTRE", centre.id); db.commit()
    return {"id": centre.id, "is_active": centre.is_active}


def _operator_dict(user: AdminUser) -> dict:
    return {"id": user.id, "full_name": user.full_name, "username": user.username, "mobile": user.mobile,
            "centre_id": user.centre_id, "centre": user.centre.name if user.centre else None,
            "is_active": user.is_active, "created_at": user.created_at, "last_login": user.last_login}


@master_router.get("/centres/{centre_id}/operators")
def centre_operators(centre_id: int, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    _centre_for_master(db, master, centre_id)
    return [_operator_dict(u) for u in db.query(AdminUser).filter(AdminUser.centre_id == centre_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).all()]


@master_router.post("/operators", status_code=201)
def create_operator(payload: OperatorPayload, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    _centre_for_master(db, master, payload.centre_id)
    if db.query(AdminUser.id).filter(func.lower(AdminUser.username) == payload.username.strip().lower()).first(): raise HTTPException(409, "Username already exists")
    user = AdminUser(full_name=payload.full_name, username=payload.username.strip(), mobile=payload.mobile,
                     password_hash=hash_password(payload.password), role=RoleEnum.CENTRE_OPERATOR,
                     centre_id=payload.centre_id, district_id=master.district_id, is_active=payload.is_active)
    db.add(user); db.flush(); db.add(OperatorProfile(user_id=user.id, centre_id=user.centre_id, status="ACTIVE" if user.is_active else "INACTIVE")); _audit(db, master, "CREATE_OPERATOR", "OPERATOR", user.id); db.commit(); db.refresh(user)
    return _operator_dict(user)


def _operator_for_master(db: Session, master: AdminUser, operator_id: int) -> AdminUser:
    user = db.query(AdminUser).filter(AdminUser.id == operator_id, AdminUser.role == RoleEnum.CENTRE_OPERATOR).first()
    if not user: raise HTTPException(404, "Operator not found")
    _centre_for_master(db, master, user.centre_id); return user


@master_router.put("/operators/{operator_id}")
def update_operator(operator_id: int, payload: OperatorUpdate, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    user = _operator_for_master(db, master, operator_id)
    if payload.username is not None:
        username = payload.username.strip()
        if not username:
            raise HTTPException(400, "Username cannot be empty")
        duplicate = db.query(AdminUser.id).filter(
            func.lower(AdminUser.username) == username.lower(), AdminUser.id != user.id
        ).first()
        if duplicate:
            raise HTTPException(409, "Username already exists")
        user.username = username
    for key, value in payload.model_dump(exclude_unset=True, exclude={"password", "username"}).items(): setattr(user, key, value)
    if payload.password: user.password_hash = hash_password(payload.password)
    _audit(db, master, "UPDATE_OPERATOR", "OPERATOR", user.id); db.commit(); return _operator_dict(user)


@master_router.put("/operators/{operator_id}/status")
def operator_status(operator_id: int, payload: StatusPayload, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    user = _operator_for_master(db, master, operator_id); user.is_active = payload.is_active
    _audit(db, master, "UPDATE_OPERATOR_STATUS", "OPERATOR", user.id); db.commit(); return _operator_dict(user)


@master_router.put("/operators/{operator_id}/centre")
def operator_centre(operator_id: int, payload: CentreAssignment, master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    user = _operator_for_master(db, master, operator_id); _centre_for_master(db, master, payload.centre_id); user.centre_id = payload.centre_id
    profile = db.query(OperatorProfile).filter(OperatorProfile.user_id == user.id).first()
    if profile: profile.centre_id = payload.centre_id
    _audit(db, master, "ASSIGN_OPERATOR", "OPERATOR", user.id); db.commit(); return _operator_dict(user)


def _district_records(model, master, db):
    return db.query(model).join(Booking).join(Centre).filter(Centre.district_id == master.district_id)


@master_router.get("/bookings")
def district_bookings(master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    return db.query(Booking).join(Centre).filter(Centre.district_id == master.district_id).order_by(Booking.created_at.desc()).limit(500).all()


@master_router.get("/queue")
def district_queue(master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    return db.query(Booking).join(Centre).filter(Centre.district_id == master.district_id, Booking.status.in_([BookingStatusEnum.WAITING, BookingStatusEnum.CALLED, BookingStatusEnum.SERVING])).all()


@master_router.get("/procurement")
def district_procurement(master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    return _district_records(Procurement, master, db).all()


@master_router.get("/payments")
def district_payments(master: AdminUser = Depends(_master), db: Session = Depends(get_db)):
    return _district_records(Payment, master, db).all()


def _master_dict(user: AdminUser) -> dict:
    return {"id": user.id, "full_name": user.full_name, "username": user.username, "mobile": user.mobile,
            "district_id": user.district_id, "district": user.district.name if user.district else None,
            "is_active": user.is_active, "created_at": user.created_at, "last_login": user.last_login}


@super_router.get("/masters")
def list_masters(_: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    return [_master_dict(u) for u in db.query(AdminUser).filter(AdminUser.role == RoleEnum.MASTER).order_by(AdminUser.created_at.desc()).all()]


@super_router.get("/districts")
def list_districts(_: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    """Return the configured Tamil Nadu districts for MASTER assignment."""
    return [{"id": d.id, "name": d.name, "code": d.code, "state": d.state, "status": d.status}
            for d in db.query(District).order_by(District.name).all()]


@super_router.post("/masters", status_code=201)
def create_master(payload: MasterPayload, super_admin: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    district = db.query(District).filter(District.id == payload.district_id).first()
    if not district: raise HTTPException(404, "District not found")
    if db.query(AdminUser.id).filter(func.lower(AdminUser.username) == payload.username.strip().lower()).first(): raise HTTPException(409, "Username already exists")
    user = AdminUser(full_name=payload.full_name, username=payload.username.strip(), mobile=payload.mobile,
                     password_hash=hash_password(payload.password), role=RoleEnum.MASTER,
                     district_id=district.id, centre_id=None, is_active=payload.is_active)
    db.add(user); db.flush(); db.add(MasterProfile(user_id=user.id, district_id=district.id)); _audit(db, super_admin, "CREATE_MASTER", "MASTER", user.id); db.commit(); db.refresh(user)
    return _master_dict(user)


@super_router.get("/masters/{master_id}")
def get_master(master_id: int, _: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.id == master_id, AdminUser.role == RoleEnum.MASTER).first()
    if not user: raise HTTPException(404, "Master not found")
    return _master_dict(user)


@super_router.put("/masters/{master_id}")
def update_master(master_id: int, payload: MasterUpdate, super_admin: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.id == master_id, AdminUser.role == RoleEnum.MASTER).first()
    if not user: raise HTTPException(404, "Master not found")
    if payload.district_id is not None and not db.query(District.id).filter(District.id == payload.district_id).first(): raise HTTPException(404, "District not found")
    for key, value in payload.model_dump(exclude_unset=True, exclude={"password"}).items(): setattr(user, key, value)
    if payload.password: user.password_hash = hash_password(payload.password)
    profile = db.query(MasterProfile).filter(MasterProfile.user_id == user.id).first()
    if profile and payload.district_id is not None: profile.district_id = payload.district_id
    _audit(db, super_admin, "UPDATE_MASTER", "MASTER", user.id); db.commit(); return _master_dict(user)


@super_router.put("/masters/{master_id}/status")
def master_status(master_id: int, payload: StatusPayload, super_admin: AdminUser = Depends(_super), db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.id == master_id, AdminUser.role == RoleEnum.MASTER).first()
    if not user: raise HTTPException(404, "Master not found")
    user.is_active = payload.is_active; _audit(db, super_admin, "UPDATE_MASTER_STATUS", "MASTER", user.id); db.commit(); return _master_dict(user)
