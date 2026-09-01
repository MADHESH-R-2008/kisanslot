from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Procurement
from schemas import ProcurementResponse, ProcurementUpdateRequest
from auth import get_current_farmer

router = APIRouter(prefix="/api/procurement", tags=["Procurement"])


@router.get("/{booking_id}", response_model=ProcurementResponse)
def get_procurement(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get procurement status for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    if booking.farmer_id != farmer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    procurement = db.query(Procurement).filter(Procurement.booking_id == booking.id).first()
    if not procurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement record not found.")

    return ProcurementResponse(
        crop=booking.crop,
        expected_quantity=booking.expected_quantity,
        actual_weight=procurement.actual_weight,
        quality_status=procurement.quality_status,
        rate=procurement.rate,
        total_amount=procurement.total_amount,
        status=procurement.status.value,
    )


@router.put("/{booking_id}", response_model=ProcurementResponse)
def update_procurement(
    booking_id: str,
    req: ProcurementUpdateRequest,
    db: Session = Depends(get_db),
):
    """Admin/test endpoint to update procurement status."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    procurement = db.query(Procurement).filter(Procurement.booking_id == booking.id).first()
    if not procurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement record not found.")

    if req.quality_status is not None:
        procurement.quality_status = req.quality_status
    if req.actual_weight is not None:
        procurement.actual_weight = req.actual_weight
    if req.rate is not None:
        procurement.rate = req.rate
    if req.total_amount is not None:
        procurement.total_amount = req.total_amount
    if req.status is not None:
        procurement.status = req.status

    db.commit()
    db.refresh(procurement)

    return ProcurementResponse(
        crop=booking.crop,
        expected_quantity=booking.expected_quantity,
        actual_weight=procurement.actual_weight,
        quality_status=procurement.quality_status,
        rate=procurement.rate,
        total_amount=procurement.total_amount,
        status=procurement.status if isinstance(procurement.status, str) else procurement.status.value,
    )
