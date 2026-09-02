"""
KisanSlot — Database Seed Script
Populates test data: farmer, centres, slots, and a sample booking.
Run: python seed.py
"""

from datetime import date, time, datetime
from database import SessionLocal, engine, Base
from models import (
    Farmer, Centre, Slot, Booking, Procurement, Payment, AdminUser,
    BookingStatusEnum, ProcurementStatusEnum, PaymentStatusEnum,
)
from auth import hash_password


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ─── Check if already seeded ─────────────────────────
        existing_farmer = db.query(Farmer).filter(Farmer.mobile == "9876543210").first()
        if existing_farmer:
            print("⚠️  Database already seeded. Skipping.")
            print(f"   Test Farmer: {existing_farmer.name} ({existing_farmer.mobile})")
            print(f"   Password: 123456")
            return

        print(" Seeding KisanSlot database...")

        # ─── Farmer ─────────────────────────────────────────
        farmer = Farmer(
            name="Ravi Kumar",
            mobile="9876543210",
            farmer_id="FR10245",
            village="Example Village",
            district="Example District",
            state="Tamil Nadu",
            crop="Paddy",
            expected_quantity=850.0,
            password_hash=hash_password("123456"),
        )
        db.add(farmer)
        db.flush()  # Get the farmer.id
        print(f"   ✅ Farmer: {farmer.name} (Mobile: {farmer.mobile}, Password: 123456)")

        # ─── Centres ────────────────────────────────────────
        centres = [
            Centre(
                name="Centre A",
                address="APMC Market Yard, North Block, Main Road",
                district="Example District",
                state="Tamil Nadu",
                latitude=11.0168,
                longitude=76.9558,
                active_counters=4,
                is_active=True,
                distance_km=4.0,
                rating=4.2,
            ),
            Centre(
                name="Centre B",
                address="Taluk Regulated Agricultural Market, Highway Junction",
                district="Example District",
                state="Tamil Nadu",
                latitude=11.0245,
                longitude=76.9612,
                active_counters=3,
                is_active=True,
                distance_km=7.0,
                rating=4.9,
            ),
            Centre(
                name="Centre C",
                address="District Farmers Co-operative Hub, Sector 4",
                district="Example District",
                state="Tamil Nadu",
                latitude=11.0312,
                longitude=76.9701,
                active_counters=2,
                is_active=True,
                distance_km=10.0,
                rating=4.5,
            ),
        ]
        db.add_all(centres)
        db.flush()
        print(f"   ✅ Centres: {len(centres)} centres created")

        # ─── Admin Users ───────────────────────────────────────
        operator = AdminUser(
            username="admin",
            password_hash=hash_password("admin123"),
            centre_id=centres[0].id,
            role="CENTRE_OPERATOR"
        )
        # Phase 3.1 required accounts
        operator1 = AdminUser(
            username="operator1",
            password_hash=hash_password("op123"),
            centre_id=centres[2].id,  # Centre C (id 3)
            role="CENTRE_OPERATOR"
        )
        admin_user = AdminUser(
            username="admin_user",
            password_hash=hash_password("admin123"),
            centre_id=None,
            role="ADMIN"
        )
        super_admin = AdminUser(
            username="super",
            password_hash=hash_password("super123"),
            centre_id=None,
            role="SUPER_ADMIN"
        )
        master = AdminUser(
            username="master",
            password_hash=hash_password("master123"),
            centre_id=None,
            role="SUPER_ADMIN"
        )
        db.add_all([operator, operator1, admin_user, super_admin, master])
        db.flush()
        print(f"   ✅ Operator: {operator.username} (Centre: {centres[0].name}, Password: admin123)")
        print(f"   ✅ Operator1: {operator1.username} (Centre: {centres[2].name}, Password: op123)")
        print(f"   ✅ Admin: {admin_user.username} (Password: admin123)")
        print(f"   ✅ Super Admin: {super_admin.username} (Password: super123)")
        print(f"   ✅ Master Admin: {master.username} (Role: {master.role}, Password: master123)")


        # ─── Slots ──────────────────────────────────────────
        slot_times = [
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
        ]

        dates = [
            date(2026, 8, 25),
            date(2026, 8, 26),
            date(2026, 8, 27),
        ]

        slots_created = 0
        for centre in centres:
            for d in dates:
                for i, (start, end) in enumerate(slot_times):
                    # Make one slot full for demo (12:00-13:00 on Aug 25 at Centre A)
                    booked = 25 if (centre.name == "Centre A" and d == date(2026, 8, 25) and i == 3) else 0

                    slot = Slot(
                        centre_id=centre.id,
                        date=d,
                        start_time=start,
                        end_time=end,
                        capacity=25,
                        booked_count=booked,
                        is_active=True,
                    )
                    db.add(slot)
                    slots_created += 1

        db.flush()
        print(f"   ✅ Slots: {slots_created} time slots created (3 centres × 3 dates × 6 slots)")

        # ─── Sample Booking ─────────────────────────────────
        # Book Ravi Kumar at Centre B, 25 Aug, 10:00-11:00
        centre_b = centres[1]
        slot_10am_aug25 = (
            db.query(Slot)
            .filter(
                Slot.centre_id == centre_b.id,
                Slot.date == date(2026, 8, 25),
                Slot.start_time == time(10, 0),
            )
            .first()
        )

        if slot_10am_aug25:
            booking = Booking(
                booking_id="KS1025",
                farmer_id=farmer.id,
                centre_id=centre_b.id,
                slot_id=slot_10am_aug25.id,
                crop="Paddy",
                expected_quantity=850.0,
                vehicle_number="TN 01 AB 1234",
                token_number=17,
                status=BookingStatusEnum.CONFIRMED,
            )
            db.add(booking)
            slot_10am_aug25.booked_count += 1
            db.flush()

            # Procurement record
            procurement = Procurement(
                booking_id=booking.id,
                quality_status="PENDING",
                rate=21.50,
                status=ProcurementStatusEnum.PENDING,
            )
            db.add(procurement)

            # Payment record
            payment = Payment(
                booking_id=booking.id,
                amount=18275.00,
                status=PaymentStatusEnum.PROCESSING,
            )
            db.add(payment)

            print(f"   ✅ Booking: {booking.booking_id} (Token #{booking.token_number})")

        db.commit()

        print()
        print("🎉 Seed completed successfully!")
        print()
        print("┌─────────────────────────────────────────┐")
        print("│  TEST LOGIN CREDENTIALS                 │")
        print("├─────────────────────────────────────────┤")
        print("│  Mobile:   9876543210                   │")
        print("│  Password: 123456                       │")
        print("│  Name:     Ravi Kumar                   │")
        print("│  Farmer ID: FR10245                     │")
        print("├─────────────────────────────────────────┤")
        print("│  CENTRE OPERATOR CREDENTIALS            │")
        print("├─────────────────────────────────────────┤")
        print("│  Username: admin                        │")
        print("│  Password: admin123                     │")
        print("├─────────────────────────────────────────┤")
        print("│  MASTER ADMIN CREDENTIALS               │")
        print("├─────────────────────────────────────────┤")
        print("│  Username: master                       │")
        print("│  Password: master123                    │")
        print("└─────────────────────────────────────────┘")

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
