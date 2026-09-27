from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from datetime import datetime

from models import AdminUser, Farmer, Booking, Payment, PaymentStatusEnum, ProcurementStatusEnum
from schemas import PaymentResponse, PaymentUpdateRequest
from auth import get_current_farmer, get_current_admin

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("/{booking_id}", response_model=PaymentResponse)
def get_payment(
    booking_id: str,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Get payment status for a booking."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    if booking.farmer_id != farmer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    return PaymentResponse(
        amount=payment.amount,
        transaction_id=payment.transaction_id,
        status=payment.status.value,
        payment_date=payment.payment_date,
    )


def _admin_payment(booking_id: str, admin: AdminUser, db: Session):
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if admin.centre_id is not None and booking.centre_id != admin.centre_id:
        raise HTTPException(status_code=403, detail="Not authorized for this centre.")
    if not booking.payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")
    if not booking.procurement or booking.procurement.status != ProcurementStatusEnum.COMPLETED:
        raise HTTPException(status_code=409, detail="Procurement must be completed before payment processing.")
    booking.payment.amount = booking.procurement.total_amount
    return booking, booking.payment


def _notify_payment(db: Session, booking: Booking, old_status: str, new_status: str):
    if old_status == new_status:
        return
    from services.notification_service import create_notification
    messages = {
        "PROCESSING": ("PAYMENT_PROCESSING", "Payment Processing", "Your payment is currently being processed."),
        "COMPLETED": ("PAYMENT_COMPLETED", "Payment Completed", "Your payment has been successfully completed."),
        "FAILED": ("PAYMENT_FAILED", "Payment Failed", "Your payment could not be completed. Please contact the procurement centre."),
    }
    if new_status in messages:
        kind, title, message = messages[new_status]
        create_notification(db, booking.farmer_id, kind, title, message, booking.id, booking.centre_id)


def _payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        amount=payment.amount,
        transaction_id=payment.transaction_id,
        status=payment.status.value if hasattr(payment.status, "value") else str(payment.status),
        payment_date=payment.payment_date,
    )


@router.post("/{booking_id}/process", response_model=PaymentResponse)
def process_payment(booking_id: str, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    booking, payment = _admin_payment(booking_id, admin, db)
    old_status = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
    if old_status not in ["PENDING", "FAILED"]:
        raise HTTPException(status_code=409, detail="Payment cannot be moved to processing from its current status.")
    payment.status = PaymentStatusEnum.PROCESSING
    db.commit()
    _notify_payment(db, booking, old_status, "PROCESSING")
    db.refresh(payment)
    return _payment_response(payment)


@router.post("/{booking_id}/complete", response_model=PaymentResponse)
def complete_payment(booking_id: str, req: PaymentUpdateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    booking, payment = _admin_payment(booking_id, admin, db)
    old_status = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
    if old_status != "PROCESSING":
        raise HTTPException(status_code=409, detail="Payment must be processing before completion.")
    payment.status = PaymentStatusEnum.COMPLETED
    payment.transaction_id = req.transaction_id
    if not payment.transaction_id:
        raise HTTPException(status_code=400, detail="Transaction reference is required.")
    payment.payment_date = req.payment_date or datetime.utcnow()
    db.commit()
    _notify_payment(db, booking, old_status, "COMPLETED")
    db.refresh(payment)
    return _payment_response(payment)


@router.post("/{booking_id}/failed", response_model=PaymentResponse)
def fail_payment(booking_id: str, req: PaymentUpdateRequest, admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    booking, payment = _admin_payment(booking_id, admin, db)
    old_status = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
    if old_status != "PROCESSING":
        raise HTTPException(status_code=409, detail="Only a processing payment can fail.")
    payment.status = PaymentStatusEnum.FAILED
    payment.transaction_id = req.transaction_id
    db.commit()
    _notify_payment(db, booking, old_status, "FAILED")
    db.refresh(payment)
    return _payment_response(payment)


@router.put("/{booking_id}", response_model=PaymentResponse, deprecated=True)
def update_payment(
    booking_id: str,
    req: PaymentUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Compatibility endpoint. The amount always comes from procurement."""
    booking, payment = _admin_payment(booking_id, admin, db)

    old_status = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)

    if req.transaction_id is not None:
        payment.transaction_id = req.transaction_id
    if req.status is not None:
        requested = req.status.upper()
        if requested == "PAID":
            requested = "COMPLETED"
        allowed = {"PENDING": {"PROCESSING"}, "FAILED": {"PROCESSING"}, "PROCESSING": {"COMPLETED", "FAILED"}}
        if requested not in allowed.get(old_status, set()):
            raise HTTPException(status_code=409, detail=f"Invalid payment transition: {old_status} -> {requested}")
        if requested == "COMPLETED" and not payment.transaction_id:
            raise HTTPException(status_code=400, detail="Transaction reference is required.")
        payment.status = requested
    if req.payment_date is not None:
        payment.payment_date = req.payment_date

    db.commit()
    db.refresh(payment)

    try:
        new_status = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
        _notify_payment(db, booking, old_status, new_status)
    except Exception:
        pass

    return _payment_response(payment)
