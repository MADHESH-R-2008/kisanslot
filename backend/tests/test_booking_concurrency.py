from concurrent.futures import ThreadPoolExecutor

from conftest import auth_header
from database import SessionLocal
from models import Booking, Slot


def test_capacity_and_token_allocation_are_atomic(client):
    payload = {"centre_id": 3, "slot_id": 1, "crop": "Paddy", "expected_quantity": 10, "vehicle_number": "TN01AA0001"}

    def book(farmer_id):
        return client.post("/api/bookings", json=payload, headers=auth_header(farmer_id, "FARMER"))

    with ThreadPoolExecutor(max_workers=3) as pool:
        responses = list(pool.map(book, (1, 2, 3)))

    assert sorted(response.status_code for response in responses) == [201, 409, 409], [response.json() for response in responses]
    db = SessionLocal()
    slot = db.query(Slot).get(1)
    bookings = db.query(Booking).all()
    assert slot.booked_count == 1
    assert len(bookings) == 1
    assert len({(b.centre_id, b.booking_date, b.token_number) for b in bookings}) == 1
    db.close()
