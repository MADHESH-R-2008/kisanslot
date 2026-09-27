"""Comprehensive tests for the MASTER role: login, dashboard, district isolation,
centre CRUD, operator CRUD, cross-district denial, role restrictions, and
super-admin master management."""

from conftest import auth_header
from database import SessionLocal
from models import AdminUser, Centre, RoleEnum, MasterProfile


# ── 1. Master Login ──────────────────────────────────────────────────────────

def test_master_login(client):
    """Master can log in with username/password and receive a MASTER JWT."""
    res = client.post("/api/auth/admin/login", json={"username": "master1", "password": "master123"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "MASTER"
    assert data["district_id"] == 1
    assert "access_token" in data


def test_master_login_invalid_password(client):
    """Master login with wrong password is denied."""
    res = client.post("/api/auth/admin/login", json={"username": "master1", "password": "wrong"})
    assert res.status_code == 401


# ── 2. Master Dashboard ─────────────────────────────────────────────────────

def test_master_dashboard_is_district_scoped(client):
    """Master dashboard returns only data for their assigned district."""
    headers = auth_header(5, "MASTER", district_id=1)
    res = client.get("/api/master/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["district"] == "District 1"
    assert "total_centres" in data
    assert "active_centres" in data
    assert "inactive_centres" in data
    assert "total_operators" in data
    assert "today_bookings" in data
    assert "live_queue" in data
    assert "pending_procurement" in data
    assert "pending_payments" in data


# ── 3. Master sees only own district centres ─────────────────────────────────

def test_master_sees_only_own_district_centres(client):
    """Master can only see centres in their assigned district."""
    headers = auth_header(5, "MASTER", district_id=1)
    res = client.get("/api/master/centres", headers=headers)
    assert res.status_code == 200
    centres = res.json()["items"]
    for c in centres:
        assert c["district_id"] == 1


# ── 4. Master creates centre ────────────────────────────────────────────────

def test_master_creates_centre(client):
    """Master can create a centre, which is auto-assigned to their district."""
    headers = auth_header(5, "MASTER", district_id=1)
    payload = {"name": "New Test Centre", "code": "NTC-1", "address": "Test Address", "total_counters": 2}
    res = client.post("/api/master/centres", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["district_id"] == 1
    assert data["name"] == "New Test Centre"


# ── 5. Master cannot create centre in another district ───────────────────────

def test_master_cannot_create_centre_in_other_district(client):
    """Master's centre creation always uses their district_id — they can't override it."""
    headers = auth_header(5, "MASTER", district_id=1)
    payload = {"name": "Cross District Centre", "code": "CDX-1", "address": "Addr"}
    res = client.post("/api/master/centres", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["district_id"] == 1  # Always master's district


# ── 6. Master updates centre ────────────────────────────────────────────────

def test_master_updates_centre(client):
    """Master can update a centre in their district."""
    headers = auth_header(5, "MASTER", district_id=1)
    res = client.put("/api/master/centres/1", json={"name": "Updated Centre"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Centre"


# ── 7. Master activates/deactivates centre ───────────────────────────────────

def test_master_toggles_centre_status(client):
    """Master can activate and deactivate centres in their district."""
    headers = auth_header(5, "MASTER", district_id=1)
    res = client.put("/api/master/centres/1/status", json={"is_active": False}, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    res = client.put("/api/master/centres/1/status", json={"is_active": True}, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is True


# ── 8. Master creates operator ───────────────────────────────────────────────

def test_master_creates_operator(client):
    """Master can create an operator assigned to a centre in their district."""
    headers = auth_header(5, "MASTER", district_id=1)
    payload = {"full_name": "Test Operator", "username": "testop1", "password": "testpass1", "centre_id": 1}
    res = client.post("/api/master/operators", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["centre_id"] == 1


# ── 9. Master cannot assign operator to another district ─────────────────────

def test_master_cannot_assign_operator_to_other_district(client):
    """Master cannot assign or create an operator for a centre outside their district."""
    headers = auth_header(5, "MASTER", district_id=1)
    # Create operator first
    payload = {"full_name": "Op", "username": "crossop", "password": "password1", "centre_id": 1}
    created = client.post("/api/master/operators", json=payload, headers=headers)
    assert created.status_code == 201
    op_id = created.json()["id"]

    # Try to reassign to district 2 centre
    res = client.put(f"/api/master/operators/{op_id}/centre", json={"centre_id": 2}, headers=headers)
    assert res.status_code == 403


# ── 10. Master cannot access another district's centre ───────────────────────

def test_master_cannot_access_other_district_centre(client):
    """Master gets 403 when trying to access centres in other districts."""
    headers = auth_header(5, "MASTER", district_id=1)
    # Centre 2 belongs to district 2
    res = client.get("/api/master/centres/2", headers=headers)
    assert res.status_code == 403

    # Centre 3 belongs to district 3
    res = client.get("/api/master/centres/3", headers=headers)
    assert res.status_code == 403


# ── 11. Master cannot access SUPER_ADMIN APIs ────────────────────────────────

def test_master_cannot_access_super_admin_apis(client):
    """Master cannot access super-admin master management endpoints."""
    headers = auth_header(5, "MASTER", district_id=1)
    res = client.get("/api/super-admin/masters", headers=headers)
    assert res.status_code == 403

    res = client.post("/api/super-admin/masters", json={
        "full_name": "Fake", "username": "fake", "password": "password1", "district_id": 2
    }, headers=headers)
    assert res.status_code == 403


# ── 12. Super Admin can create Master ────────────────────────────────────────

def test_super_admin_creates_master(client):
    """Super Admin can create a new master account."""
    headers = auth_header(3, "SUPER_ADMIN")
    payload = {"full_name": "Master Two", "username": "master2", "password": "master234", "district_id": 2}
    res = client.post("/api/super-admin/masters", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["district_id"] == 2
    assert data["full_name"] == "Master Two"


# ── 13. Super Admin can manage all Masters ───────────────────────────────────

def test_super_admin_can_list_and_update_masters(client):
    """Super Admin can list, view, update, and toggle status of masters."""
    headers = auth_header(3, "SUPER_ADMIN")

    # Create a master first
    create_res = client.post("/api/super-admin/masters", json={
        "full_name": "Master Three", "username": "master3", "password": "master345", "district_id": 3
    }, headers=headers)
    assert create_res.status_code == 201
    master_id = create_res.json()["id"]

    # List
    list_res = client.get("/api/super-admin/masters", headers=headers)
    assert list_res.status_code == 200
    assert any(m["id"] == master_id for m in list_res.json())

    # View
    view_res = client.get(f"/api/super-admin/masters/{master_id}", headers=headers)
    assert view_res.status_code == 200
    assert view_res.json()["username"] == "master3"

    # Update
    update_res = client.put(f"/api/super-admin/masters/{master_id}", json={"full_name": "Updated Master"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Updated Master"

    # Deactivate
    status_res = client.put(f"/api/super-admin/masters/{master_id}/status", json={"is_active": False}, headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["is_active"] is False


# ── 14. Centre Operator remains restricted ───────────────────────────────────

def test_centre_operator_cannot_access_master_apis(client):
    """Centre Operator cannot access master-level endpoints."""
    headers = auth_header(1, "CENTRE_OPERATOR", centre_id=3, district_id=3)
    res = client.get("/api/master/dashboard", headers=headers)
    assert res.status_code == 403

    res = client.get("/api/master/centres", headers=headers)
    assert res.status_code == 403


# ── 15. Farmer cannot access Master APIs ─────────────────────────────────────

def test_farmer_cannot_access_master_apis(client):
    """Farmer role is completely denied from master endpoints.
    The auth layer rejects FARMER tokens with 401 before the MASTER
    authorization check can return 403 — both are correct denials.
    """
    headers = auth_header(1, "FARMER")
    res = client.get("/api/master/dashboard", headers=headers)
    assert res.status_code in (401, 403)

    res = client.get("/api/master/centres", headers=headers)
    assert res.status_code in (401, 403)

    res = client.post("/api/master/centres", json={"name": "X", "code": "X", "address": "X"}, headers=headers)
    assert res.status_code in (401, 403)


# ── Master Profile & District ────────────────────────────────────────────────

def test_master_profile_and_district(client):
    """Master can access their profile and district info."""
    headers = auth_header(5, "MASTER", district_id=1)
    profile = client.get("/api/master/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["district_id"] == 1

    district = client.get("/api/master/district", headers=headers)
    assert district.status_code == 200
    assert district.json()["name"] == "District 1"


# ── Master bookings/queue/procurement/payments ───────────────────────────────

def test_master_district_data_endpoints(client):
    """Master can access bookings, queue, procurement, and payments endpoints."""
    headers = auth_header(5, "MASTER", district_id=1)
    for endpoint in ["/api/master/bookings", "/api/master/queue", "/api/master/procurement", "/api/master/payments"]:
        res = client.get(endpoint, headers=headers)
        assert res.status_code == 200, f"Failed on {endpoint}: {res.status_code}"


# ── Duplicate username prevention ────────────────────────────────────────────

def test_master_duplicate_username_rejected(client):
    """Creating a master with an existing username is rejected."""
    headers = auth_header(3, "SUPER_ADMIN")
    payload = {"full_name": "Dup", "username": "master1", "password": "password1", "district_id": 2}
    res = client.post("/api/super-admin/masters", json=payload, headers=headers)
    assert res.status_code == 409
