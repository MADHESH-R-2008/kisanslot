import os
import sys
from datetime import datetime

# Add current directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base, ensure_schema_up_to_date
from models import Farmer, Booking, Notification, NotificationPreference, Centre, Slot
from services.notification_service import create_notification, notification_service
from routes.notification_routes import build_user_notifications_query

def run_tests():
    print("=== Testing KisanSlot Notification Module ===")

    # 1. Ensure DB schema migration succeeds
    print("1. Running schema auto-migration...")
    Base.metadata.create_all(bind=engine)
    results = ensure_schema_up_to_date(engine)
    print("   Schema migration completed successfully.")

    db = SessionLocal()
    try:
        # 2. Get or create test farmer
        farmer = db.query(Farmer).first()
        if not farmer:
            print("   No farmer found. Run seed first!")
            return

        print(f"2. Testing notification creation for Farmer: {farmer.name} (ID: {farmer.id})...")

        # 3. Create test notifications across types
        n1 = create_notification(
            db=db,
            user_id=farmer.id,
            notification_type="BOOKING_CONFIRMED",
            title="Booking Confirmed",
            message="Your slot at Centre C has been confirmed.\nToken: C3-006",
        )
        assert n1 is not None and n1.id is not None, "Failed to create BOOKING_CONFIRMED notification"

        n2 = create_notification(
            db=db,
            user_id=farmer.id,
            notification_type="FARMER_CALLED",
            title="Your Turn",
            message="Token C3-006 has been called.\nPlease proceed to Counter 2.",
        )
        assert n2 is not None, "Failed to create FARMER_CALLED notification"

        n3 = create_notification(
            db=db,
            user_id=farmer.id,
            notification_type="PAYMENT_COMPLETED",
            title="Payment Completed",
            message="Your payment has been successfully completed.\nTransaction: DBT-KS-10006",
        )
        assert n3 is not None, "Failed to create PAYMENT_COMPLETED notification"

        print("   Created notifications successfully!")

        # 4. Test security query builder
        farmer_user = {"user_id": farmer.id, "role": "FARMER"}
        query = build_user_notifications_query(db, farmer_user)
        user_notifications = query.all()
        print(f"3. Security Check: Farmer can access {len(user_notifications)} notifications.")
        assert len(user_notifications) >= 3, "Farmer query returned fewer notifications than expected."

        # 5. Test unread count logic
        unread_count = query.filter(Notification.is_read == False).count()
        print(f"4. Unread Count Check: {unread_count} unread notifications.")
        assert unread_count >= 3, "Unread count mismatch"

        # 6. Test mark as read logic
        n1.is_read = True
        db.commit()
        new_unread_count = query.filter(Notification.is_read == False).count()
        assert new_unread_count == unread_count - 1, "Mark read did not decrement unread count."
        print(f"5. Mark Read Check: Unread count decremented properly to {new_unread_count}.")

        # 7. Test user preference mute check
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == farmer.id).first()
        if not pref:
            pref = NotificationPreference(user_id=farmer.id, booking_notifications=False)
            db.add(pref)
        else:
            pref.booking_notifications = False
        db.commit()

        muted = create_notification(
            db=db,
            user_id=farmer.id,
            notification_type="BOOKING_CONFIRMED",
            title="Muted Booking",
            message="This should be muted by preference",
        )
        assert muted is None, "Muted notification was created despite preference set to False!"
        print("6. User Preference Mute Check: Muted notification was correctly blocked.")

        # Re-enable preference
        pref.booking_notifications = True
        db.commit()

        print("\n[SUCCESS] All Notification Module backend tests passed successfully!")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
