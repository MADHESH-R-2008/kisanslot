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

    return PaymentResponse(
        amount=payment.amount,
        transaction_id=payment.transaction_id,
        status=payment.status if isinstance(payment.status, str) else payment.status.value,
        payment_date=payment.payment_date,
    )
