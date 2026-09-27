from datetime import date, time

from conftest import auth_header
from database import SessionLocal
from models import Booking, BookingStatusEnum, Counter, Payment, Procurement, Slot


def _workflow_booking(reference="KS-FLOW", token=1):
    db = SessionLocal()
    slot = Slot(centre_id=3, date=date.today(), start_time=time(11), end_time=time(12), capacity=5, booked_count=1, is_active=True)
    db.add(slot); db.flush()
    booking = Booking(booking_id=reference, farmer_id=1, centre_id=3, slot_id=slot.id, booking_date=date.today(), crop="Paddy", expected_quantity=10, vehicle_number="TN01AA0001", token_number=token, status=BookingStatusEnum.WAITING)
    db.add(booking); db.flush()
    db.add_all([Procurement(booking_id=booking.id), Payment(booking_id=booking.id), Counter(centre_id=3, name="Counter 1")])
    db.commit(); db.close()


def test_queue_procurement_payment_state_machines(client):
    _workflow_booking()
    operator = auth_header(1, "CENTRE_OPERATOR", 3, 3)

    called = client.post("/api/queue/centres/3/next", headers=operator)
    assert called.status_code == 200 and called.json()["status"] == "CALLED"
    assert client.post("/api/queue/KS-FLOW/complete", headers=operator).status_code == 409
    assert client.post("/api/queue/KS-FLOW/start", headers=operator).json()["status"] == "SERVING"

    assert client.post("/api/procurement/KS-FLOW/start", headers=operator).status_code == 200
    assert client.post("/api/procurement/KS-FLOW/start", headers=operator).status_code == 409
    completed = client.post("/api/procurement/KS-FLOW/complete", headers=operator, json={"accepted_quantity": 8, "rejected_quantity": 2, "quality_grade": "A", "procurement_rate": 2300})
    assert completed.status_code == 200 and completed.json()["total_amount"] == 18400
    assert client.post("/api/procurement/KS-FLOW/complete", headers=operator, json={"accepted_quantity": 8, "procurement_rate": 2300}).status_code == 409

    assert client.post("/api/payments/KS-FLOW/complete", headers=operator, json={"transaction_id": "TX-1"}).status_code == 409
    assert client.post("/api/payments/KS-FLOW/process", headers=operator).status_code == 200
    paid = client.post("/api/payments/KS-FLOW/complete", headers=operator, json={"transaction_id": "TX-1"})
    assert paid.status_code == 200 and paid.json()["amount"] == 18400
    assert client.post("/api/payments/KS-FLOW/complete", headers=operator, json={"transaction_id": "TX-2"}).status_code == 409
    assert client.post("/api/queue/KS-FLOW/complete", headers=operator).json()["status"] == "COMPLETED"
    assert client.post("/api/queue/KS-FLOW/start", headers=operator).status_code == 409


def test_wrong_centre_operator_is_rejected(client):
    _workflow_booking("KS-WRONG", 2)
    assert client.post("/api/queue/KS-WRONG/start", headers=auth_header(1, "CENTRE_OPERATOR", 1)).status_code == 401
