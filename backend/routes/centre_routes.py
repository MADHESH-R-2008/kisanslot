from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Centre, AdminUser, RoleEnum
from schemas import CentreResponse, CentreCreateRequest, CentreUpdateRequest
from dependencies import get_current_admin, require_admin_or_super, enforce_operator_centre

router = APIRouter(prefix="/api/centres", tags=["Centres"])

# Public endpoint: list all centres (no auth required)
@router.get("/", response_model=List[CentreResponse])
def list_centres(db: Session = Depends(get_db)):
    centres = db.query(Centre).all()
    return centres

# Create centre – ADMIN or SUPER_ADMIN can create centres
@router.post("/", response_model=CentreResponse)
def create_centre(
    payload: CentreCreateRequest,
    admin: dict = Depends(require_admin_or_super()),
    db: Session = Depends(get_db),
):
    # Ensure the caller has sufficient role
    if admin.get("role") not in [RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin or Super Admin accounts can create centres",
        )
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
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A centre with this code already exists",
        )
    db.refresh(centre)
    return centre

# Update centre – ADMIN/SUPER_ADMIN can update any centre; CENTRE_OPERATOR can update only its own centre
@router.put("/{centre_id}", response_model=CentreResponse)
def update_centre(
    centre_id: int,
    payload: CentreUpdateRequest,
    admin: dict = Depends(require_admin_or_super()),
    db: Session = Depends(get_db),
    allowed: bool = Depends(enforce_operator_centre),
):
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    # Apply only the fields supplied by the client
    for attr, value in payload.dict(exclude_unset=True).items():
        setattr(centre, attr, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A centre with this code already exists",
        )
    db.refresh(centre)
    return centre

# Delete centre – only SUPER_ADMIN can delete centres
@router.delete("/{centre_id}")
def delete_centre(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if admin.role.value != RoleEnum.SUPER_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Super Admin can delete centres")
    centre = db.query(Centre).filter(Centre.id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    db.delete(centre)
    db.commit()
    return {"message": "Centre deleted"}
