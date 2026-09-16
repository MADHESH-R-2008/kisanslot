"""
KisanSlot — Database Seed Script (Phase 3.2)
Populates test data: farmer, centres, slots, sample bookings, counters, and queue demo data.
Run: python seed.py
"""

from datetime import date, time, datetime, timedelta
from database import SessionLocal, engine, Base
from models import (
    Farmer, Centre, Slot, Booking, Procurement, Payment, AdminUser, Counter, Notification,
    BookingStatusEnum, ProcurementStatusEnum, PaymentStatusEnum, CounterStatusEnum,
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
            print("⚠️  Database already seeded. Skipping core data.")
            print(f"   Test Farmer: {existing_farmer.name} ({existing_farmer.mobile})")
            print(f"   Password: 123456")

            # Still ensure today's slots and counters exist
            _ensure_today_slots(db)
            _ensure_counters(db)
            _ensure_queue_demo_data(db, existing_farmer)
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

        # ─── Additional test farmers for queue demo ──────────
        demo_farmers = []
        for i in range(1, 9):
            f = Farmer(
                name=f"Farmer Demo {i}",
                mobile=f"900000000{i}",
                farmer_id=f"FD{10000+i}",
                village=f"Village {i}",
                district="Example District",
                state="Tamil Nadu",
                crop=["Paddy", "Wheat", "Cotton", "Sugarcane", "Maize", "Rice", "Sorghum", "Groundnut"][i-1],
                expected_quantity=100.0 * i,
                password_hash=hash_password("demo123"),
            )
            db.add(f)
            demo_farmers.append(f)
        db.flush()
        print(f"   ✅ Demo Farmers: {len(demo_farmers)} created (password: demo123)")

        # ─── Centres ────────────────────────────────────────
        centres = [
            Centre(
                name="Centre A",
                code="CTR-A",
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
                code="CTR-B",
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
                code="CTR-C",
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

        # Include original dates + today + next 3 days
        today = date.today()
        dates = [
            date(2026, 8, 25),
            date(2026, 8, 26),
            date(2026, 8, 27),
        ]
        # Add today and upcoming days (avoid duplicates)
        for i in range(4):
            d = today + timedelta(days=i)
            if d not in dates:
                dates.append(d)

        slots_created = 0
        for centre in centres:
            for d in dates:
                for i, (start, end) in enumerate(slot_times):
                    # Check if slot already exists
                    existing = db.query(Slot).filter(
                        Slot.centre_id == centre.id,
                        Slot.date == d,
                        Slot.start_time == start,
                    ).first()
                    if existing:
                        continue

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
        print(f"   ✅ Slots: {slots_created} time slots created")

        # ─── Counters ────────────────────────────────────────
        _create_counters(db, centres)

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

        # ─── Queue Demo Data for Centre C ────────────────────
        _create_queue_demo_bookings(db, centres[2], demo_farmers)

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
        print("│  OPERATOR1 (Centre C) CREDENTIALS       │")
        print("├─────────────────────────────────────────┤")
        print("│  Username: operator1                    │")
        print("│  Password: op123                        │")
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


def _create_counters(db, centres):
    """Create counters for each centre if they don't exist."""
    counter_configs = {
        0: [("Counter 1", "ACTIVE"), ("Counter 2", "ACTIVE"), ("Counter 3", "ACTIVE"), ("Counter 4", "ACTIVE")],
        1: [("Counter 1", "ACTIVE"), ("Counter 2", "ACTIVE"), ("Counter 3", "ACTIVE")],
        2: [("Counter 1", "ACTIVE"), ("Counter 2", "ACTIVE"), ("Counter 3", "ACTIVE"), ("Counter 4", "INACTIVE")],
    }

    for idx, centre in enumerate(centres):
        existing = db.query(Counter).filter(Counter.centre_id == centre.id).count()
        if existing > 0:
            continue

        for name, status in counter_configs.get(idx, [("Counter 1", "ACTIVE")]):
            counter = Counter(
                centre_id=centre.id,
                name=name,
                status=status,
                is_available=(status == "ACTIVE"),
            )
            db.add(counter)

    db.flush()
    print("   ✅ Counters: Created for all centres")


def _ensure_today_slots(db):
    """Ensure today's slots exist for all centres."""
    today = date.today()
    centres = db.query(Centre).filter(Centre.is_active == True).all()
    slot_times = [
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
    ]

    created = 0
    for centre in centres:
        for i in range(4):
            d = today + timedelta(days=i)
            existing = db.query(Slot).filter(
                Slot.centre_id == centre.id,
                Slot.date == d,
            ).first()
            if not existing:
                for start, end in slot_times:
                    slot = Slot(
                        centre_id=centre.id,
                        date=d,
                        start_time=start,
                        end_time=end,
                        capacity=25,
                        booked_count=0,
                        is_active=True,
                    )
                    db.add(slot)
                    created += 1
    if created:
        db.commit()
        print(f"   ✅ Added {created} today/upcoming slots")


def _ensure_counters(db):
    """Ensure counters exist for all centres."""
    centres = db.query(Centre).filter(Centre.is_active == True).all()
    for centre in centres:
        existing = db.query(Counter).filter(Counter.centre_id == centre.id, Counter.is_deleted == False).count()
        if existing == 0:
            for i in range(1, 4):
                counter = Counter(
                    centre_id=centre.id,
                    name=f"Counter {i}",
                    status="ACTIVE",
                    is_available=True,
                )
                db.add(counter)
    db.commit()
    print("   ✅ Counters verified")


def _ensure_queue_demo_data(db, farmer):
    """Create demo queue bookings for Centre C if none exist today."""
    today = date.today()
    centre_c = db.query(Centre).filter(Centre.code == "CTR-C").first()
    if not centre_c:
        return

    # Check if we already have today's demo bookings
    existing_today = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_c.id, Slot.date == today)
        .count()
    )
    if existing_today > 0:
        print("   ⚠️  Queue demo data already exists for today")
        return

    # Get demo farmers
    demo_farmers = db.query(Farmer).filter(Farmer.mobile.like("90000000%")).all()
    if not demo_farmers:
        return

    _create_queue_demo_bookings(db, centre_c, demo_farmers)
    db.commit()
    print("   ✅ Queue demo data created for today")


def _create_queue_demo_bookings(db, centre_c, demo_farmers):
    """Create sample bookings in various queue states for demo."""
    today = date.today()

    # Get today's first available slot for Centre C
    slot = (
        db.query(Slot)
        .filter(Slot.centre_id == centre_c.id, Slot.date == today, Slot.is_active == True)
        .order_by(Slot.start_time.asc())
        .first()
    )
    if not slot:
        print("   ⚠️  No slots available for Centre C today — skipping demo bookings")
        return

    # Get the highest existing booking number
    last = db.query(Booking).order_by(Booking.id.desc()).first()
    next_num = 1001
    if last and last.booking_id.startswith("KS"):
        try:
            next_num = int(last.booking_id[2:]) + 1
        except ValueError:
            pass

    statuses = [
        BookingStatusEnum.COMPLETED,
        BookingStatusEnum.COMPLETED,
        BookingStatusEnum.SERVING,
        BookingStatusEnum.CALLED,
        BookingStatusEnum.WAITING,
        BookingStatusEnum.WAITING,
        BookingStatusEnum.WAITING,
        BookingStatusEnum.SKIPPED,
    ]

    crops = ["Paddy", "Wheat", "Cotton", "Sugarcane", "Maize", "Rice", "Sorghum", "Groundnut"]

    for i, (farmer, booking_status) in enumerate(zip(demo_farmers[:len(statuses)], statuses)):
        token_num = i + 1
        booking = Booking(
            booking_id=f"KS{next_num + i}",
            farmer_id=farmer.id,
            centre_id=centre_c.id,
            slot_id=slot.id,
            crop=crops[i % len(crops)],
            expected_quantity=100.0 * (i + 1),
            vehicle_number=f"TN 0{i+1} CD {1000+i}",
            token_number=token_num,
            status=booking_status,
        )

        # Set timestamps for realistic demo
        now = datetime.utcnow()
        if booking_status in [BookingStatusEnum.COMPLETED]:
            booking.call_time = now - timedelta(minutes=30 + i * 5)
            booking.serving_at = now - timedelta(minutes=25 + i * 5)
            booking.completed_at = now - timedelta(minutes=15 + i * 5)
            booking.assigned_counter = 1 if i == 0 else 2
        elif booking_status == BookingStatusEnum.SERVING:
            booking.call_time = now - timedelta(minutes=10)
            booking.serving_at = now - timedelta(minutes=5)
            booking.assigned_counter = 1
        elif booking_status == BookingStatusEnum.CALLED:
            booking.call_time = now - timedelta(minutes=2)
            booking.assigned_counter = 2
        elif booking_status == BookingStatusEnum.SKIPPED:
            booking.call_time = now - timedelta(minutes=20)

        db.add(booking)
        slot.booked_count += 1

        # Create procurement/payment for each
        db.flush()
        proc = Procurement(
            booking_id=booking.id,
            quality_status="COMPLETED" if booking_status == BookingStatusEnum.COMPLETED else "PENDING",
            rate=21.50,
            status=ProcurementStatusEnum.COMPLETED if booking_status == BookingStatusEnum.COMPLETED else ProcurementStatusEnum.PENDING,
        )
        pay = Payment(
            booking_id=booking.id,
            amount=booking.expected_quantity * 21.50,
            status=PaymentStatusEnum.COMPLETED if booking_status == BookingStatusEnum.COMPLETED else PaymentStatusEnum.PENDING,
        )
        db.add(proc)
        db.add(pay)

    # Update counter BUSY status for serving/called bookings
    counters = db.query(Counter).filter(Counter.centre_id == centre_c.id, Counter.is_deleted == False).order_by(Counter.id).all()
    if len(counters) >= 2:
        # Counter 1 is BUSY (serving)
        serving_booking = db.query(Booking).filter(
            Booking.centre_id == centre_c.id,
            Booking.status == BookingStatusEnum.SERVING,
        ).first()
        if serving_booking and counters[0]:
            counters[0].status = CounterStatusEnum.BUSY
            counters[0].current_booking_id = serving_booking.id
            counters[0].is_available = False

        # Counter 2 is BUSY (called)
        called_booking = db.query(Booking).filter(
            Booking.centre_id == centre_c.id,
            Booking.status == BookingStatusEnum.CALLED,
        ).first()
        if called_booking and counters[1]:
            counters[1].status = CounterStatusEnum.BUSY
            counters[1].current_booking_id = called_booking.id
            counters[1].is_available = False

    db.flush()
    print(f"   ✅ Queue Demo: {len(statuses)} bookings created for Centre C (today)")


if __name__ == "__main__":
    seed()
