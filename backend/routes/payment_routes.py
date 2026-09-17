from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Farmer, Booking, Payment
from schemas import PaymentResponse, PaymentUpdateRequest
from auth import get_current_farmer

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


@router.put("/{booking_id}", response_model=PaymentResponse)
def update_payment(
    booking_id: str,
    req: PaymentUpdateRequest,
    db: Session = Depends(get_db),
):
    """Admin/test endpoint to update payment status."""
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found.")

    old_status = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)

    if req.amount is not None:
        payment.amount = req.amount
    if req.transaction_id is not None:
        payment.transaction_id = req.transaction_id
    if req.status is not None:
        payment.status = req.status
    if req.payment_date is not None:
        payment.payment_date = req.payment_date

    db.commit()
    db.refresh(payment)

    # Trigger notifications based on payment status
    try:
        from services.notification_service import create_notification
        new_status = payment.status.value if hasattr(payment.status, 'value') else str(payment.status)
        tx_id = payment.transaction_id or f"DBT-KS-1000{booking.id}"

        if new_status == "PROCESSING" and old_status != "PROCESSING":
            create_notification(
                db=db,
                user_id=booking.farmer_id,
                notification_type="PAYMENT_PROCESSING",
                title="Payment Processing",
                message="Your payment is currently being processed.",
                booking_id=booking.id,
                centre_id=booking.centre_id,
            )
        elif new_status == "COMPLETED" and old_status != "COMPLETED":
            create_notification(
                db=db,
                user_id=booking.farmer_id,
                notification_type="PAYMENT_COMPLETED",
                title="Payment Completed",
                message=f"Your payment has been successfully completed.\nTransaction: {tx_id}",
                booking_id=booking.id,
                centre_id=booking.centre_id,
            )
        elif new_status == "FAILED" and old_status != "FAILED":
            create_notification(
                db=db,
                user_id=booking.farmer_id,
                notification_type="PAYMENT_FAILED",
                title="Payment Failed",
                message="Your payment could not be completed. Please contact the procurement centre.",
                booking_id=booking.id,
                centre_id=booking.centre_id,
            )
    except Exception:
        pass

    return PaymentResponse(
        amount=payment.amount,
        transaction_id=payment.transaction_id,
        status=payment.status if isinstance(payment.status, str) else payment.status.value,
        payment_date=payment.payment_date,
    )
