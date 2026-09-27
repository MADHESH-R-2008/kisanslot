import os
import sys
from datetime import date, time, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
test_database_url = os.environ.get("TEST_DATABASE_URL", "sqlite:///./backend/tests/test_kisanslot.db")
if os.environ.get("DATABASE_URL") and test_database_url == os.environ["DATABASE_URL"]:
    raise RuntimeError("TEST_DATABASE_URL must not be the same as DATABASE_URL")
if os.environ.get("TEST_DATABASE_URL") and os.environ.get("ALLOW_DESTRUCTIVE_TEST_DATABASE") != "true":
    raise RuntimeError("Set ALLOW_DESTRUCTIVE_TEST_DATABASE=true to confirm the test database may be dropped")
os.environ["DATABASE_URL"] = test_database_url
os.environ["SECRET_KEY"] = "test-only-secret-key-with-sufficient-length"

from auth import create_access_token, hash_password  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402
from models import AdminUser, Centre, District, Farmer, MasterProfile, RoleEnum, Slot  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    districts = [District(id=i, name=f"District {i}", code=f"DIST-{i}", state="State", status="ACTIVE") for i in (1, 2, 3)]
    db.add_all(districts)
    db.flush()
    centres = [
        Centre(id=i, name=f"Centre {chr(64+i)}", code=f"CTR-{i}", address="Address", district=f"District {i}", district_id=i, state="State", total_counters=2, active_counters=2)
        for i in (1, 2, 3)
    ]
    db.add_all(centres)
    farmers = [
        Farmer(name="Farmer One", mobile="9999999991", farmer_id="F001", village="V", district="D", state="S", crop="Paddy", expected_quantity=10, password_hash=hash_password("farmer123")),
        Farmer(name="Farmer Two", mobile="9999999992", farmer_id="F002", village="V", district="D", state="S", crop="Paddy", expected_quantity=10, password_hash=hash_password("farmer123")),
        Farmer(name="Farmer Three", mobile="9999999993", farmer_id="F003", village="V", district="D", state="S", crop="Paddy", expected_quantity=10, password_hash=hash_password("farmer123")),
    ]
    db.add_all(farmers)
    db.add_all([
        AdminUser(username="operator1", password_hash=hash_password("op123456"), role=RoleEnum.CENTRE_OPERATOR, centre_id=3, district_id=3),
        AdminUser(username="admin", password_hash=hash_password("admin123"), role=RoleEnum.ADMIN),
        AdminUser(username="super", password_hash=hash_password("super123"), role=RoleEnum.SUPER_ADMIN),
        AdminUser(username="inactive", password_hash=hash_password("inactive123"), role=RoleEnum.CENTRE_OPERATOR, centre_id=3, is_active=False),
    ])
    master = AdminUser(username="master1", full_name="Master One", password_hash=hash_password("master123"), role=RoleEnum.MASTER, district_id=1)
    db.add(master)
    db.flush()
    db.add(MasterProfile(user_id=master.id, district_id=1))
    db.add(Slot(id=1, centre_id=3, date=date.today() + timedelta(days=1), start_time=time(9), end_time=time(10), capacity=1, booked_count=0, is_active=True))
    db.commit()
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(user_id: int, role: str, centre_id=None, district_id=None, expires_delta=None):
    token = create_access_token({"sub": str(user_id), "user_id": user_id, "role": role, "centre_id": centre_id, "district_id": district_id}, expires_delta=expires_delta)
    return {"Authorization": f"Bearer {token}"}
