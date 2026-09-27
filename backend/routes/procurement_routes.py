from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Procurement, AdminUser, Payment, ProcurementStatusEnum
from schemas import ProcurementResponse, ProcurementUpdateRequest
from auth import get_current_farmer, get_current_admin

router = APIRouter(prefix="/api/procurement", tags=["Procurement"])


def _decimal(value, field: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field} must be a valid number.")


def _require_admin_booking(booking_id: str, admin: AdminUser, db: Session) -> Booking:
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if admin.centre_id is not None and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Not authorized for this centre.")
    if not booking.procurement:
        raise HTTPException(status_code=404, detail="Procurement record not found.")
    return booking


@router.get("/centre/{centre_id}")
def list_centre_procurement(
    centre_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return procurement rows for the admin dashboard table."""
    if admin.centre_id is not None and admin.centre_id != centre_id:
        raise HTTPException(status_code=403, detail="Not authorized for this centre.")

    bookings = (
        db.query(Booking)
        .filter(Booking.centre_id == centre_id, Booking.is_deleted.is_(False))
        .order_by(Booking.token_number.asc())
        .all()
    )
    return [
        {
            "id": booking.procurement.id if booking.procurement else booking.id,
            "booking_id": booking.booking_id,
            "token_number": booking.token_number,
            "farmer": {"name": booking.farmer.name if booking.farmer else None},
            "booking": {
                "crop": booking.crop,
                "expected_quantity": booking.expected_quantity,
            },
            "actual_quantity": booking.procurement.actual_weight if booking.procurement else None,
            "grade": booking.procurement.quality_status if booking.procurement else None,
            "price_per_quintal": booking.procurement.rate if booking.procurement else None,
            "payment_amount": booking.procurement.total_amount if booking.procurement else None,
            "status": (
                booking.procurement.status.value
                if booking.procurement and hasattr(booking.procurement.status, "value")
                else booking.procurement.status if booking.procurement else "PENDING"
            ),
        }
        for booking in bookings
    ]


@router.post("/{booking_id}/start")
def start_admin_procurement(
    booking_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    booking = _require_admin_booking(booking_id, admin, db)
    if booking.status in ["CANCELLED", "SKIPPED", "NO_SHOW"]:
        raise HTTPException(status_code=409, detail="Procurement cannot start for this booking state.")
    if booking.procurement.status != ProcurementStatusEnum.PENDING:
        raise HTTPException(status_code=409, detail="Procurement has already started.")
    booking.procurement.status = ProcurementStatusEnum.QUALITY_CHECK
    db.commit()
    return {"message": "Procurement started", "booking_id": booking_id}


@router.post("/{booking_id}/complete")
@router.put("/{booking_id}/complete", deprecated=True)
def complete_admin_procurement(
    booking_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    booking = _require_admin_booking(booking_id, admin, db)
    procurement = booking.procurement
    if procurement.status not in [ProcurementStatusEnum.QUALITY_CHECK, ProcurementStatusEnum.WEIGHING]:
        raise HTTPException(status_code=409, detail="Procurement must be in progress before completion.")
    accepted_quantity = _decimal(data.get("accepted_quantity", data.get("actual_quantity", 0)), "accepted_quantity")
    rejected_quantity = _decimal(data.get("rejected_quantity", 0), "rejected_quantity")
    rate = _decimal(data.get("procurement_rate", data.get("price_per_quintal", procurement.rate or 0)), "procurement_rate")
    if accepted_quantity < 0 or rejected_quantity < 0 or rate <= 0:
        raise HTTPException(status_code=400, detail="Quantities must be non-negative and rate must be positive.")
    if accepted_quantity + rejected_quantity > Decimal(str(booking.expected_quantity)):
        raise HTTPException(status_code=400, detail="Accepted and rejected quantities exceed the booked quantity.")
    procurement.actual_weight = accepted_quantity
    procurement.rejected_quantity = rejected_quantity
    procurement.quality_status = str(data.get("quality_grade", data.get("grade", "A")))
    procurement.rate = rate
    procurement.total_amount = (accepted_quantity * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    procurement.remarks = data.get("remarks")
    procurement.procurement_date = datetime.utcnow()
    procurement.status = ProcurementStatusEnum.COMPLETED
    if booking.payment:
        booking.payment.amount = procurement.total_amount
    db.commit()
    try:
        from services.notification_service import create_notification
        create_notification(
            db=db,
            user_id=booking.farmer_id,
            notification_type="PROCUREMENT_COMPLETED",
            title="Procurement Completed",
            message="Your procurement has been completed.",
            booking_id=booking.id,
            centre_id=booking.centre_id,
        )
    except Exception:
        pass
    return {
        "message": "Procurement completed",
        "booking_id": booking_id,
        "total_amount": procurement.total_amount,
    }

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

    if admin.centre_id is not None and booking.centre_id != admin.centre_id:
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

    if admin.centre_id is not None and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this centre.")

    procurement = db.query(Procurement).filter(Procurement.booking_id == booking.id).first()
    if not procurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement record not found.")

    old_status = procurement.status.value if hasattr(procurement.status, 'value') else str(procurement.status)

    if req.quality_status is not None:
        procurement.quality_status = req.quality_status
    if req.rate is not None:
        if req.rate <= 0:
            raise HTTPException(status_code=400, detail="Rate must be positive.")
        procurement.rate = _decimal(req.rate, "rate")
    if req.actual_weight is not None:
        if req.actual_weight < 0 or req.actual_weight > booking.expected_quantity:
            raise HTTPException(status_code=400, detail="Actual quantity is invalid.")
        procurement.actual_weight = _decimal(req.actual_weight, "actual_weight")
        procurement.total_amount = (procurement.actual_weight * procurement.rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if req.status is not None:
        requested = req.status.upper()
        allowed = {"PENDING": {"QUALITY_CHECK", "WEIGHING"}, "QUALITY_CHECK": {"WEIGHING", "COMPLETED"}, "WEIGHING": {"COMPLETED"}}
        if requested not in allowed.get(old_status, set()):
            raise HTTPException(status_code=409, detail=f"Invalid procurement transition: {old_status} -> {requested}")
        procurement.status = requested

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
