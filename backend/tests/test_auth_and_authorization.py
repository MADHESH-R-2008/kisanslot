from datetime import timedelta

from conftest import auth_header
from database import SessionLocal
from models import Booking, BookingStatusEnum, Notification, Payment, PaymentStatusEnum, Procurement, Slot


def _booking_for(farmer_id: int, reference: str, token: int):
    db = SessionLocal()
    slot = db.query(Slot).get(1)
    booking = Booking(booking_id=reference, farmer_id=farmer_id, centre_id=3, slot_id=1, booking_date=slot.date, crop="Paddy", expected_quantity=10, vehicle_number="TN01AA0001", token_number=token, status=BookingStatusEnum.WAITING)
    db.add(booking)
    db.flush()
    db.add(Procurement(booking_id=booking.id))
    db.add(Payment(booking_id=booking.id, status=PaymentStatusEnum.PENDING))
    db.commit()
    db.close()


def test_login_and_invalid_credentials(client):
    ok = client.post("/api/auth/login", json={"mobile": "9999999991", "password": "farmer123"})
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    assert client.post("/api/auth/login", json={"mobile": "9999999991", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/admin/login", json={"username": "missing", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/admin/login", json={"username": "inactive", "password": "inactive123"}).status_code == 403


def test_bad_missing_expired_and_wrong_role_tokens(client):
    assert client.get("/api/bookings/my").status_code == 401
    assert client.get("/api/bookings/my", headers={"Authorization": "Bearer malformed"}).status_code == 401
    assert client.get("/api/bookings/my", headers=auth_header(1, "FARMER", expires_delta=timedelta(seconds=-1))).status_code == 401
    assert client.get("/api/bookings/my", headers=auth_header(1, "ADMIN")).status_code == 401


def test_farmer_cannot_access_other_booking_or_payment(client):
    _booking_for(1, "KS-ONE", 1)
    assert client.get("/api/bookings/KS-ONE", headers=auth_header(1, "FARMER")).status_code == 200
    assert client.get("/api/bookings/KS-ONE", headers=auth_header(2, "FARMER")).status_code == 403
    assert client.get("/api/payments/KS-ONE", headers=auth_header(1, "FARMER")).status_code == 200
    assert client.get("/api/payments/KS-ONE", headers=auth_header(2, "FARMER")).status_code == 403


def test_operator_centre_scope_and_admin_access(client):
    operator = auth_header(1, "CENTRE_OPERATOR", 3, 3)
    assert client.get("/api/queue/centre/3/status", headers=operator).status_code == 200
    assert client.get("/api/queue/centre/1/status", headers=operator).status_code == 403
    assert client.get("/api/queue/centre/2/status", headers=operator).status_code == 403
    assert client.get("/api/admin/operators", headers=operator).status_code == 403
    assert client.get("/api/admin/operators", headers=auth_header(2, "ADMIN")).status_code == 200
    assert client.get("/api/admin/analytics/overview", headers=auth_header(3, "SUPER_ADMIN")).status_code == 403
    assert client.get("/api/queue/centre/3/status", headers=auth_header(1, "CENTRE_OPERATOR", 1)).status_code == 401


def test_farmer_notification_isolation(client):
    db = SessionLocal()
    first = Notification(user_id=1, type="SYSTEM", title="First", message="For farmer one")
    second = Notification(user_id=2, type="SYSTEM", title="Second", message="For farmer two")
    db.add_all([first, second])
    db.commit()
    second_id = second.id
    db.close()

    response = client.get("/api/notifications", headers=auth_header(1, "FARMER"))
    assert response.status_code == 200
    assert [item["title"] for item in response.json()["items"]] == ["First"]
    assert client.put(f"/api/notifications/{second_id}/read", headers=auth_header(1, "FARMER")).status_code == 404


def test_management_lists_and_farmer_history_are_scoped(client):
    _booking_for(1, "KS-HISTORY", 1)
    admin = auth_header(2, "ADMIN")
    operator = auth_header(1, "CENTRE_OPERATOR", 3, 3)
    assert client.get("/api/admin/farmers/1/history", headers=admin).status_code == 200
    assert client.get("/api/admin/payments", headers=operator).status_code == 200
    assert client.get("/api/admin/procurements", headers=operator).status_code == 200
    assert client.get("/api/admin/payments?centre_id=1", headers=operator).status_code == 403
    assert client.get("/api/admin/procurements?centre_id=2", headers=operator).status_code == 403
