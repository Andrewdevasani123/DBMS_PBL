import os
import sys
import pytest

# Ensure blood_bank_project directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
import db

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client

def set_authenticated_session(client, user_id=1, username="admin", role="admin"):
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": user_id,
            "username": username,
            "full_name": "Test Administrator",
            "role": role,
            "email": f"{username}@bloodbank.org"
        }
        sess["_csrf_token"] = "mock_test_csrf_token"
    return "mock_test_csrf_token"

# -------------------------------------------------------------------------
# Test Case 1: Admin Login
# -------------------------------------------------------------------------
def test_01_admin_login(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "token123"

    response = client.post("/login", data={
        "csrf_token": "token123",
        "username": "admin",
        "password": "Admin@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "user" in sess
        assert sess["user"]["role"] == "admin"
        assert sess["user"]["username"] == "admin"

# -------------------------------------------------------------------------
# Test Case 2: Staff Login
# -------------------------------------------------------------------------
def test_02_staff_login(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "token123"

    response = client.post("/login", data={
        "csrf_token": "token123",
        "username": "staff_rahul",
        "password": "Staff@123"
    }, follow_redirects=True)

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "user" in sess
        assert sess["user"]["role"] == "staff"
        assert sess["user"]["username"] == "staff_rahul"

# -------------------------------------------------------------------------
# Test Case 3: Unauthorized Access Protection
# -------------------------------------------------------------------------
def test_03_unauthorized_access(client):
    # Unauthenticated access to dashboard should redirect to /login
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # Unauthenticated access to donor management should redirect
    response = client.get("/donors", follow_redirects=False)
    assert response.status_code == 302

    # Staff trying to access Admin-only route (/users) should redirect to dashboard
    set_authenticated_session(client, user_id=2, username="staff_rahul", role="staff")
    response = client.get("/users", follow_redirects=False)
    assert response.status_code == 302
    assert "/dashboard" in response.headers["Location"]

# -------------------------------------------------------------------------
# Test Case 4: Donor Registration
# -------------------------------------------------------------------------
def test_04_donor_registration(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")
    
    unique_phone = "9820099999"
    # Ensure phone not present
    db.execute_db("DELETE FROM donors WHERE phone = %s", (unique_phone,))

    response = client.post("/donors/add", data={
        "csrf_token": csrf,
        "full_name": "Test Automated Donor",
        "age": "29",
        "gender": "Male",
        "blood_group": "A+",
        "phone": unique_phone,
        "email": "auto.donor@test.com",
        "address": "404 Test Residency, Mumbai"
    }, follow_redirects=True)

    assert response.status_code == 200
    donor = db.query_db("SELECT * FROM donors WHERE phone = %s", (unique_phone,), one=True)
    assert donor is not None
    assert donor["full_name"] == "Test Automated Donor"
    assert donor["blood_group"] == "A+"
    assert donor["age"] == 29

# -------------------------------------------------------------------------
# Test Case 5: Donation Recording
# -------------------------------------------------------------------------
def test_05_donation_recording(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    donor = db.query_db("SELECT donor_id FROM donors WHERE is_active = 1 LIMIT 1", one=True)
    donor_id = donor["donor_id"]

    response = client.post("/donations/add", data={
        "csrf_token": csrf,
        "donor_id": donor_id,
        "units_donated": "1",
        "donation_date": "2026-10-11",
        "status": "Pending",
        "remarks": "Automated pytest test donation"
    }, follow_redirects=True)

    assert response.status_code == 200
    donation = db.query_db("SELECT * FROM donations WHERE donor_id = %s ORDER BY donation_id DESC LIMIT 1", (donor_id,), one=True)
    assert donation is not None
    assert donation["status"] == "Pending"
    assert donation["inventory_updated"] == 0

# -------------------------------------------------------------------------
# Test Case 6: Inventory Increase Upon Accepted Donation
# -------------------------------------------------------------------------
def test_06_inventory_increase(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    # Pick a donor with blood group O+
    donor = db.query_db("SELECT donor_id, blood_group FROM donors WHERE blood_group = 'O+' AND is_active = 1 LIMIT 1", one=True)
    assert donor is not None

    inv_before = db.query_db("SELECT available_units FROM inventory WHERE blood_group = 'O+'", one=True)["available_units"]

    # Record accepted donation of 2 units
    response = client.post("/donations/add", data={
        "csrf_token": csrf,
        "donor_id": donor["donor_id"],
        "units_donated": "2",
        "donation_date": "2026-10-11",
        "status": "Accepted",
        "remarks": "Automated stock increment verification"
    }, follow_redirects=True)

    assert response.status_code == 200
    inv_after = db.query_db("SELECT available_units FROM inventory WHERE blood_group = 'O+'", one=True)["available_units"]
    assert inv_after == inv_before + 2

# -------------------------------------------------------------------------
# Test Case 7: Blood Request Creation
# -------------------------------------------------------------------------
def test_07_blood_request_creation(client):
    csrf = set_authenticated_session(client, user_id=2, username="staff_rahul", role="staff")

    response = client.post("/requests/add", data={
        "csrf_token": csrf,
        "patient_name": "Pytest Emergency Patient",
        "hospital_name": "City General Trauma Hospital",
        "blood_group": "O+",
        "units_required": "1"
    }, follow_redirects=True)

    assert response.status_code == 200
    req = db.query_db("SELECT * FROM blood_requests WHERE patient_name = 'Pytest Emergency Patient' ORDER BY request_id DESC LIMIT 1", one=True)
    assert req is not None
    assert req["status"] == "Pending"
    assert req["units_required"] == 1

# -------------------------------------------------------------------------
# Test Case 8 & 9: Blood Issue Processing & Inventory Decrease
# -------------------------------------------------------------------------
def test_08_and_09_blood_issue_and_inventory_decrease(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    # Approve the request created in Test 7
    req = db.query_db("SELECT * FROM blood_requests WHERE patient_name = 'Pytest Emergency Patient' AND status = 'Pending' ORDER BY request_id DESC LIMIT 1", one=True)
    assert req is not None
    request_id = req["request_id"]

    # Approve request
    client.post(f"/requests/update-status/{request_id}", data={
        "csrf_token": csrf,
        "status": "Approved"
    }, follow_redirects=True)

    # Check inventory before issue
    inv_before = db.query_db("SELECT available_units FROM inventory WHERE blood_group = %s", (req["blood_group"],), one=True)["available_units"]

    # Process issue
    response = client.post("/issues/process", data={
        "csrf_token": csrf,
        "request_id": request_id
    }, follow_redirects=True)

    assert response.status_code == 200

    # Verify inventory decreased by 1
    inv_after = db.query_db("SELECT available_units FROM inventory WHERE blood_group = %s", (req["blood_group"],), one=True)["available_units"]
    assert inv_after == inv_before - 1

    # Verify request status is now Fulfilled
    req_updated = db.query_db("SELECT status FROM blood_requests WHERE request_id = %s", (request_id,), one=True)
    assert req_updated["status"] == "Fulfilled"

    # Verify issue record exists
    issue = db.query_db("SELECT * FROM blood_issues WHERE request_id = %s", (request_id,), one=True)
    assert issue is not None
    assert issue["units_issued"] == 1

# -------------------------------------------------------------------------
# Test Case 10: Insufficient Inventory Rejection
# -------------------------------------------------------------------------
def test_10_insufficient_inventory(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    # Create and approve request with an impossibly high unit requirement (e.g. 500 units)
    db.execute_db("""
        INSERT INTO blood_requests (patient_name, hospital_name, blood_group, units_required, request_date, status, created_by)
        VALUES ('Overdraft Test Recipient', 'Mock Hospital', 'AB-', 500, CURRENT_DATE(), 'Approved', 1)
    """)
    req = db.query_db("SELECT request_id FROM blood_requests WHERE patient_name = 'Overdraft Test Recipient'", one=True)
    req_id = req["request_id"]

    inv_before = db.query_db("SELECT available_units FROM inventory WHERE blood_group = 'AB-'", one=True)["available_units"]

    response = client.post("/issues/process", data={
        "csrf_token": csrf,
        "request_id": req_id
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Insufficient stock" in response.data

    # Ensure inventory was not changed
    inv_after = db.query_db("SELECT available_units FROM inventory WHERE blood_group = 'AB-'", one=True)["available_units"]
    assert inv_after == inv_before

    # Clean up test row
    db.execute_db("DELETE FROM blood_requests WHERE request_id = %s", (req_id,))

# -------------------------------------------------------------------------
# Test Case 11: Duplicate Issue Prevention
# -------------------------------------------------------------------------
def test_11_duplicate_issue_prevention(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    # Find an already fulfilled request
    fulfilled_req = db.query_db("SELECT request_id FROM blood_requests WHERE status = 'Fulfilled' LIMIT 1", one=True)
    assert fulfilled_req is not None
    req_id = fulfilled_req["request_id"]

    response = client.post("/issues/process", data={
        "csrf_token": csrf,
        "request_id": req_id
    }, follow_redirects=True)

    assert response.status_code == 200
    assert (b"already" in response.data) or (b"Cannot process issue" in response.data) or (b"Approved" in response.data)

# -------------------------------------------------------------------------
# Test Case 12: Invalid Form Inputs Validation
# -------------------------------------------------------------------------
def test_12_invalid_form_inputs(client):
    csrf = set_authenticated_session(client, user_id=1, username="admin", role="admin")

    # 1. Underage donor (age 14)
    response = client.post("/donors/add", data={
        "csrf_token": csrf,
        "full_name": "Underage Child",
        "age": "14",
        "gender": "Male",
        "blood_group": "O+",
        "phone": "9998881111"
    }, follow_redirects=True)
    assert b"between 18 and 65" in response.data

    # 2. Over-age donor (age 78)
    response = client.post("/donors/add", data={
        "csrf_token": csrf,
        "full_name": "Senior Citizen",
        "age": "78",
        "gender": "Female",
        "blood_group": "A+",
        "phone": "9998882222"
    }, follow_redirects=True)
    assert b"between 18 and 65" in response.data

    # 3. Invalid blood group string
    response = client.post("/donors/add", data={
        "csrf_token": csrf,
        "full_name": "Invalid Group Donor",
        "age": "25",
        "gender": "Male",
        "blood_group": "Z_POSITIVE",
        "phone": "9998883333"
    }, follow_redirects=True)
    assert b"valid donor fields" in response.data
