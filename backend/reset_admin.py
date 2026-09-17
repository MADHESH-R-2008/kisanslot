import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import AdminUser, Centre, RoleEnum
from auth import hash_password

def reset_admin_credentials():
    print("=== Resetting Admin & Centre Operator Credentials & Centre IDs ===")
    db = SessionLocal()
    try:
        centres = db.query(Centre).all()
        if not centres:
            print("No centres found. Running seed...")
            from seed import seed
            seed()
            centres = db.query(Centre).all()

        centre_c = db.query(Centre).filter(Centre.code == "CTR-C").first() or (centres[2] if len(centres) > 2 else centres[0])
        centre_a = db.query(Centre).filter(Centre.code == "CTR-A").first() or centres[0]
        centre_b = db.query(Centre).filter(Centre.code == "CTR-B").first() or (centres[1] if len(centres) > 1 else centres[0])

        users_to_reset = [
            {"username": "operator1", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_c.id},
            {"username": "operator_a", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_a.id},
            {"username": "operator_b", "password": "op123", "role": RoleEnum.CENTRE_OPERATOR, "centre_id": centre_b.id},
            {"username": "admin", "password": "admin123", "role": RoleEnum.ADMIN, "centre_id": centre_c.id},
            {"username": "super", "password": "super123", "role": RoleEnum.SUPER_ADMIN, "centre_id": None},
            {"username": "master", "password": "master123", "role": RoleEnum.SUPER_ADMIN, "centre_id": None},
        ]

        for u in users_to_reset:
            user = db.query(AdminUser).filter(AdminUser.username == u["username"]).first()
            if not user:
                user = AdminUser(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                    centre_id=u["centre_id"],
                )
                db.add(user)
            else:
                user.password_hash = hash_password(u["password"])
                user.role = u["role"]
                user.centre_id = u["centre_id"]
                user.is_active = True

            role_val = u["role"].value if hasattr(u["role"], 'value') else u["role"]
            print(f"   [SUCCESS] Reset {u['username']} -> Role: {role_val}, Centre ID: {u['centre_id']}, Pass: {u['password']}")

        db.commit()
        print("\nAll Admin & Centre Operator accounts reset successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error resetting admin credentials: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_credentials()
