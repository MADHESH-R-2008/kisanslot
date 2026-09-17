from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Procurement, AdminUser, Payment
from schemas import ProcurementResponse, ProcurementUpdateRequest
from auth import get_current_farmer, get_current_admin

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

@router.get("/admin/{booking_id}", response_model=ProcurementResponse)
def admin_get_procurement(
    booking_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint to get procurement status for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    if booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this centre.")

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
        status=procurement.status.value if not isinstance(procurement.status, str) else procurement.status,
    )

@router.put("/admin/{booking_id}", response_model=ProcurementResponse)
def update_procurement(
    booking_id: str,
    req: ProcurementUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin endpoint to update procurement status."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    if booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this centre.")

    procurement = db.query(Procurement).filter(Procurement.booking_id == booking.id).first()
    if not procurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement record not found.")

    old_status = procurement.status.value if hasattr(procurement.status, 'value') else str(procurement.status)

    if req.quality_status is not None:
        procurement.quality_status = req.quality_status
    if req.rate is not None:
        procurement.rate = req.rate
    if req.actual_weight is not None:
        procurement.actual_weight = req.actual_weight
        procurement.total_amount = req.actual_weight * procurement.rate
    if req.total_amount is not None:
        procurement.total_amount = req.total_amount
    if req.status is not None:
        procurement.status = req.status

    # Update associated payment if amount was calculated
    if procurement.total_amount is not None:
        payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
        if payment:
            payment.amount = procurement.total_amount

    db.commit()
    db.refresh(procurement)

    # Trigger notifications based on procurement status
    try:
        from services.notification_service import create_notification
        new_status = procurement.status.value if hasattr(procurement.status, 'value') else str(procurement.status)
        if new_status in ["QUALITY_CHECK", "WEIGHING", "PROCESSING"] and old_status not in ["QUALITY_CHECK", "WEIGHING", "PROCESSING", "COMPLETED"]:
            create_notification(
                db=db,
                user_id=booking.farmer_id,
                notification_type="PROCUREMENT_STARTED",
                title="Procurement Started",
                message="Your procurement process has started.",
                booking_id=booking.id,
                centre_id=booking.centre_id,
            )
        elif new_status == "COMPLETED" and old_status != "COMPLETED":
            create_notification(
                db=db,
                user_id=booking.farmer_id,
                notification_type="PROCUREMENT_COMPLETED",
                title="Procurement Completed",
                message="Your procurement has been completed successfully.",
                booking_id=booking.id,
                centre_id=booking.centre_id,
            )
    except Exception:
        pass

    return ProcurementResponse(
        crop=booking.crop,
        expected_quantity=booking.expected_quantity,
        actual_weight=procurement.actual_weight,
        quality_status=procurement.quality_status,
        rate=procurement.rate,
        total_amount=procurement.total_amount,
        status=procurement.status if isinstance(procurement.status, str) else procurement.status.value,
    )
