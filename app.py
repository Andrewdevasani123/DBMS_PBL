import os
import secrets
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import db

# Load environment configuration
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "btech_blood_bank_secure_key_2026")
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", 5))

# -------------------------------------------------------------------------
# CSRF and Context Helpers
# -------------------------------------------------------------------------
def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(16)
    return session["_csrf_token"]

app.jinja_env.globals["csrf_token"] = generate_csrf_token

def verify_csrf():
    if request.method == "POST":
        token = request.form.get("csrf_token")
        if not token or token != session.get("_csrf_token"):
            flash("Invalid security token (CSRF). Please try again.", "danger")
            return False
    return True

@app.context_processor
def inject_global_data():
    return {
        "current_user": session.get("user"),
        "now": datetime.now(),
        "low_stock_threshold": LOW_STOCK_THRESHOLD
    }

# -------------------------------------------------------------------------
# Authentication Decorators
# -------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("login"))
        if session["user"].get("role") != "admin":
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        if not verify_csrf():
            return render_template("login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("login.html")

        user = db.query_db(
            "SELECT * FROM users WHERE username = %s AND is_active = 1",
            (username,),
            one=True
        )

        if user and check_password_hash(user["password_hash"], password):
            session["user"] = {
                "id": user["user_id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
                "email": user["email"]
            }
            # Regenerate CSRF token on login
            session["_csrf_token"] = secrets.token_hex(16)
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please verify your credentials.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("login"))

# -------------------------------------------------------------------------
# Dashboard Route
# -------------------------------------------------------------------------
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    # 1. Summary Cards statistics
    total_donors = db.query_db("SELECT COUNT(*) AS total FROM donors WHERE is_active = 1", one=True)["total"]
    total_donations = db.query_db("SELECT COUNT(*) AS total FROM donations", one=True)["total"]
    available_units_res = db.query_db("SELECT COALESCE(SUM(available_units), 0) AS total FROM inventory", one=True)
    available_units = available_units_res["total"] if available_units_res else 0
    total_issues = db.query_db("SELECT COUNT(*) AS total FROM blood_issues", one=True)["total"]

    # 2. Canonical 8 Blood Groups Inventory
    inventory_items = db.query_db("""
        SELECT blood_group, available_units, last_updated 
        FROM inventory 
        ORDER BY FIELD(blood_group, 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
    """)

    # 3. Low-stock detection
    low_stock_groups = [
        item for item in inventory_items 
        if item["available_units"] <= LOW_STOCK_THRESHOLD
    ]

    # 4. Recent Donations (latest 5)
    recent_donations = db.query_db("""
        SELECT d.donation_id, d.donation_date, d.blood_group, d.units_donated, d.status,
               dn.full_name AS donor_name, u.full_name AS recorded_by_name
        FROM donations d
        JOIN donors dn ON d.donor_id = dn.donor_id
        JOIN users u ON d.recorded_by = u.user_id
        ORDER BY d.donation_id DESC
        LIMIT 5
    """)

    # 5. Recent Requests (latest 5)
    recent_requests = db.query_db("""
        SELECT r.request_id, r.patient_name, r.hospital_name, r.blood_group, 
               r.units_required, r.request_date, r.status
        FROM blood_requests r
        ORDER BY r.request_id DESC
        LIMIT 5
    """)

    return render_template(
        "dashboard.html",
        total_donors=total_donors,
        total_donations=total_donations,
        available_units=available_units,
        total_issues=total_issues,
        inventory_items=inventory_items,
        low_stock_groups=low_stock_groups,
        recent_donations=recent_donations,
        recent_requests=recent_requests
    )

# -------------------------------------------------------------------------
# Donor Management Routes
# -------------------------------------------------------------------------
@app.route("/donors")
@login_required
def donors():
    search_query = request.args.get("q", "").strip()
    blood_filter = request.args.get("blood_group", "").strip()

    sql = "SELECT * FROM donors WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (full_name LIKE %s OR phone LIKE %s OR donor_id = %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%", search_query if search_query.isdigit() else 0])

    if blood_filter:
        sql += " AND blood_group = %s"
        params.append(blood_filter)

    sql += " ORDER BY donor_id DESC"
    donor_list = db.query_db(sql, params)

    return render_template(
        "donors.html",
        donors=donor_list,
        search_query=search_query,
        blood_filter=blood_filter
    )

@app.route("/donors/add", methods=["POST"])
@login_required
def add_donor():
    if not verify_csrf():
        return redirect(url_for("donors"))

    full_name = request.form.get("full_name", "").strip()
    age = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    blood_group = request.form.get("blood_group", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip() or None
    address = request.form.get("address", "").strip() or None

    valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    valid_genders = ['Male', 'Female', 'Other']

    if not full_name or not age or not phone or blood_group not in valid_groups or gender not in valid_genders:
        flash("Please provide all required valid donor fields.", "danger")
        return redirect(url_for("donors"))

    try:
        age_int = int(age)
        if age_int < 18 or age_int > 65:
            flash("Donor age must be between 18 and 65 years.", "danger")
            return redirect(url_for("donors"))
    except ValueError:
        flash("Age must be a valid number.", "danger")
        return redirect(url_for("donors"))

    db.execute_db("""
        INSERT INTO donors (full_name, age, gender, blood_group, phone, email, address, is_active, registration_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1, CURRENT_DATE())
    """, (full_name, age_int, gender, blood_group, phone, email, address))

    flash(f"Donor '{full_name}' ({blood_group}) successfully registered!", "success")
    return redirect(url_for("donors"))

@app.route("/donors/edit/<int:donor_id>", methods=["POST"])
@login_required
def edit_donor(donor_id):
    if not verify_csrf():
        return redirect(url_for("donors"))

    full_name = request.form.get("full_name", "").strip()
    age = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()
    blood_group = request.form.get("blood_group", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip() or None
    address = request.form.get("address", "").strip() or None

    valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    valid_genders = ['Male', 'Female', 'Other']

    if not full_name or not age or not phone or blood_group not in valid_groups or gender not in valid_genders:
        flash("Invalid input data for updating donor.", "danger")
        return redirect(url_for("donors"))

    try:
        age_int = int(age)
        if age_int < 18 or age_int > 65:
            flash("Donor age must be between 18 and 65 years.", "danger")
            return redirect(url_for("donors"))
    except ValueError:
        flash("Invalid age format.", "danger")
        return redirect(url_for("donors"))

    db.execute_db("""
        UPDATE donors 
        SET full_name = %s, age = %s, gender = %s, blood_group = %s, phone = %s, email = %s, address = %s
        WHERE donor_id = %s
    """, (full_name, age_int, gender, blood_group, phone, email, address, donor_id))

    flash(f"Donor ID #{donor_id} details updated successfully.", "success")
    return redirect(url_for("donors"))

@app.route("/donors/toggle/<int:donor_id>", methods=["POST"])
@login_required
def toggle_donor(donor_id):
    if not verify_csrf():
        return redirect(url_for("donors"))

    donor = db.query_db("SELECT is_active, full_name FROM donors WHERE donor_id = %s", (donor_id,), one=True)
    if not donor:
        flash("Donor record not found.", "danger")
        return redirect(url_for("donors"))

    new_status = 0 if donor["is_active"] else 1
    db.execute_db("UPDATE donors SET is_active = %s WHERE donor_id = %s", (new_status, donor_id))

    action_label = "deactivated" if new_status == 0 else "reactivated"
    flash(f"Donor '{donor['full_name']}' has been {action_label}. Donation records remain preserved.", "info")
    return redirect(url_for("donors"))

# -------------------------------------------------------------------------
# Blood Donation Routes
# -------------------------------------------------------------------------
@app.route("/donations")
@login_required
def donations():
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()

    sql = """
        SELECT d.donation_id, d.donor_id, d.blood_group, d.donation_date, 
               d.units_donated, d.status, d.inventory_updated, d.remarks,
               dn.full_name AS donor_name, dn.phone AS donor_phone,
               u.full_name AS recorded_by_name
        FROM donations d
        JOIN donors dn ON d.donor_id = dn.donor_id
        JOIN users u ON d.recorded_by = u.user_id
        WHERE 1=1
    """
    params = []

    if search_query:
        sql += " AND (dn.full_name LIKE %s OR d.blood_group = %s)"
        params.extend([f"%{search_query}%", search_query])

    if status_filter:
        sql += " AND d.status = %s"
        params.append(status_filter)

    sql += " ORDER BY d.donation_id DESC"
    donation_list = db.query_db(sql, params)

    # Active donors for registration modal dropdown
    active_donors = db.query_db("SELECT donor_id, full_name, blood_group, phone FROM donors WHERE is_active = 1 ORDER BY full_name ASC")

    return render_template(
        "donations.html",
        donations=donation_list,
        active_donors=active_donors,
        search_query=search_query,
        status_filter=status_filter
    )

@app.route("/donations/add", methods=["POST"])
@login_required
def add_donation():
    if not verify_csrf():
        return redirect(url_for("donations"))

    donor_id = request.form.get("donor_id")
    units = request.form.get("units_donated", "1").strip()
    donation_date = request.form.get("donation_date", "").strip() or datetime.now().strftime("%Y-%m-%d")
    status = request.form.get("status", "Pending").strip()
    remarks = request.form.get("remarks", "").strip() or None

    if not donor_id:
        flash("Please select an active registered donor.", "danger")
        return redirect(url_for("donations"))

    donor = db.query_db("SELECT donor_id, full_name, blood_group, is_active FROM donors WHERE donor_id = %s", (donor_id,), one=True)
    if not donor or not donor["is_active"]:
        flash("Selected donor is inactive or invalid.", "danger")
        return redirect(url_for("donations"))

    try:
        units_int = int(units)
        if units_int <= 0:
            flash("Units donated must be a positive integer.", "danger")
            return redirect(url_for("donations"))
    except ValueError:
        flash("Units donated must be numeric.", "danger")
        return redirect(url_for("donations"))

    if status not in ["Pending", "Accepted", "Rejected"]:
        status = "Pending"

    blood_group = donor["blood_group"]
    user_id = session["user"]["id"]

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Atomic transaction: If Accepted, increment stock immediately
        if status == "Accepted":
            cursor.execute("""
                INSERT INTO donations (donor_id, blood_group, donation_date, units_donated, status, recorded_by, inventory_updated, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
            """, (donor_id, blood_group, donation_date, units_int, status, user_id, remarks))
            
            cursor.execute("""
                UPDATE inventory 
                SET available_units = available_units + %s 
                WHERE blood_group = %s
            """, (units_int, blood_group))
        else:
            cursor.execute("""
                INSERT INTO donations (donor_id, blood_group, donation_date, units_donated, status, recorded_by, inventory_updated, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s)
            """, (donor_id, blood_group, donation_date, units_int, status, user_id, remarks))

        conn.commit()
        flash(f"Donation record created for {donor['full_name']} ({blood_group}). Status: {status}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error saving donation record: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("donations"))

@app.route("/donations/update-status/<int:donation_id>", methods=["POST"])
@login_required
def update_donation_status(donation_id):
    if not verify_csrf():
        return redirect(url_for("donations"))

    new_status = request.form.get("status")
    if new_status not in ["Accepted", "Rejected"]:
        flash("Invalid status choice.", "danger")
        return redirect(url_for("donations"))

    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Lock row to prevent race conditions or duplicate additions
        cursor.execute("SELECT * FROM donations WHERE donation_id = %s FOR UPDATE", (donation_id,))
        donation = cursor.fetchone()

        if not donation:
            flash("Donation record not found.", "danger")
            conn.rollback()
            return redirect(url_for("donations"))

        if donation["status"] == "Accepted" and donation["inventory_updated"]:
            flash("This donation was already accepted and counted in inventory.", "warning")
            conn.rollback()
            return redirect(url_for("donations"))

        if new_status == "Accepted" and not donation["inventory_updated"]:
            # Increment stock and mark as counted
            cursor.execute("""
                UPDATE inventory 
                SET available_units = available_units + %s 
                WHERE blood_group = %s
            """, (donation["units_donated"], donation["blood_group"]))

            cursor.execute("""
                UPDATE donations 
                SET status = 'Accepted', inventory_updated = 1 
                WHERE donation_id = %s
            """, (donation_id,))
            flash(f"Donation #{donation_id} accepted. {donation['units_donated']} unit(s) added to {donation['blood_group']} inventory.", "success")
        elif new_status == "Rejected":
            cursor.execute("""
                UPDATE donations 
                SET status = 'Rejected' 
                WHERE donation_id = %s
            """, (donation_id,))
            flash(f"Donation #{donation_id} has been marked as Rejected.", "info")

        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Transaction failed: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("donations"))

# -------------------------------------------------------------------------
# Blood Inventory Routes
# -------------------------------------------------------------------------
@app.route("/inventory")
@login_required
def inventory():
    search_query = request.args.get("blood_group", "").strip()

    sql = """
        SELECT blood_group, available_units, last_updated 
        FROM inventory 
    """
    params = []
    if search_query:
        sql += " WHERE blood_group = %s"
        params.append(search_query)

    sql += " ORDER BY FIELD(blood_group, 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')"
    items = db.query_db(sql, params)

    total_stock = sum(item["available_units"] for item in items) if items else 0

    return render_template(
        "inventory.html",
        items=items,
        total_stock=total_stock,
        search_query=search_query
    )

# -------------------------------------------------------------------------
# Blood Request Management Routes
# -------------------------------------------------------------------------
@app.route("/requests")
@login_required
def blood_requests():
    status_filter = request.args.get("status", "").strip()
    search_query = request.args.get("q", "").strip()

    sql = """
        SELECT r.request_id, r.patient_name, r.hospital_name, r.blood_group,
               r.units_required, r.request_date, r.status, r.created_at,
               u.full_name AS created_by_name,
               i.available_units AS current_stock
        FROM blood_requests r
        JOIN users u ON r.created_by = u.user_id
        LEFT JOIN inventory i ON r.blood_group = i.blood_group
        WHERE 1=1
    """
    params = []

    if status_filter:
        sql += " AND r.status = %s"
        params.append(status_filter)

    if search_query:
        sql += " AND (r.patient_name LIKE %s OR r.hospital_name LIKE %s OR r.blood_group = %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%", search_query])

    sql += " ORDER BY r.request_id DESC"
    request_list = db.query_db(sql, params)

    return render_template(
        "requests.html",
        requests=request_list,
        status_filter=status_filter,
        search_query=search_query
    )

@app.route("/requests/add", methods=["POST"])
@login_required
def add_request():
    if not verify_csrf():
        return redirect(url_for("blood_requests"))

    patient_name = request.form.get("patient_name", "").strip()
    hospital_name = request.form.get("hospital_name", "").strip()
    blood_group = request.form.get("blood_group", "").strip()
    units_required = request.form.get("units_required", "").strip()

    valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if not patient_name or not hospital_name or blood_group not in valid_groups:
        flash("Please provide patient name, hospital name, and valid blood group.", "danger")
        return redirect(url_for("blood_requests"))

    try:
        units_int = int(units_required)
        if units_int <= 0:
            flash("Units required must be greater than zero.", "danger")
            return redirect(url_for("blood_requests"))
    except ValueError:
        flash("Units required must be a valid number.", "danger")
        return redirect(url_for("blood_requests"))

    user_id = session["user"]["id"]
    db.execute_db("""
        INSERT INTO blood_requests (patient_name, hospital_name, blood_group, units_required, request_date, status, created_by)
        VALUES (%s, %s, %s, %s, CURRENT_DATE(), 'Pending', %s)
    """, (patient_name, hospital_name, blood_group, units_int, user_id))

    flash(f"Blood request created for patient '{patient_name}' ({units_int} units of {blood_group}).", "success")
    return redirect(url_for("blood_requests"))

@app.route("/requests/update-status/<int:request_id>", methods=["POST"])
@login_required
def update_request_status(request_id):
    if not verify_csrf():
        return redirect(url_for("blood_requests"))

    new_status = request.form.get("status")
    if new_status not in ["Approved", "Rejected"]:
        flash("Invalid status decision.", "danger")
        return redirect(url_for("blood_requests"))

    req = db.query_db("SELECT * FROM blood_requests WHERE request_id = %s", (request_id,), one=True)
    if not req:
        flash("Request record not found.", "danger")
        return redirect(url_for("blood_requests"))

    if req["status"] == "Fulfilled":
        flash("Cannot change status: this request has already been fulfilled.", "warning")
        return redirect(url_for("blood_requests"))

    # If approving, check current available stock as a helpful warning
    if new_status == "Approved":
        stock = db.query_db("SELECT available_units FROM inventory WHERE blood_group = %s", (req["blood_group"],), one=True)
        avail = stock["available_units"] if stock else 0
        if avail < req["units_required"]:
            flash(f"Note: Current available stock for {req['blood_group']} ({avail} units) is less than requested ({req['units_required']} units). Blood issue will require sufficient inventory.", "warning")

    db.execute_db("UPDATE blood_requests SET status = %s WHERE request_id = %s", (new_status, request_id))
    flash(f"Request #{request_id} has been {new_status}.", "success")
    return redirect(url_for("blood_requests"))

# -------------------------------------------------------------------------
# Blood Issue Management Routes
# -------------------------------------------------------------------------
@app.route("/issues")
@login_required
def blood_issues():
    # 1. Approved requests pending blood issue
    approved_requests = db.query_db("""
        SELECT r.request_id, r.patient_name, r.hospital_name, r.blood_group,
               r.units_required, r.request_date,
               i.available_units AS current_stock
        FROM blood_requests r
        JOIN inventory i ON r.blood_group = i.blood_group
        WHERE r.status = 'Approved'
        ORDER BY r.request_id ASC
    """)

    # 2. Historical completed issues
    issue_history = db.query_db("""
        SELECT bi.issue_id, bi.request_id, bi.patient_name, bi.blood_group,
               bi.units_issued, bi.issue_date, bi.created_at,
               br.hospital_name,
               u.full_name AS issued_by_name
        FROM blood_issues bi
        JOIN blood_requests br ON bi.request_id = br.request_id
        JOIN users u ON bi.issued_by = u.user_id
        ORDER BY bi.issue_id DESC
    """)

    # Current inventory mapping
    inventory_items = db.query_db("SELECT blood_group, available_units FROM inventory")
    stock_map = {item["blood_group"]: item["available_units"] for item in inventory_items}

    return render_template(
        "issues.html",
        approved_requests=approved_requests,
        issue_history=issue_history,
        stock_map=stock_map
    )

@app.route("/issues/process", methods=["POST"])
@login_required
def process_issue():
    if not verify_csrf():
        return redirect(url_for("blood_issues"))

    request_id = request.form.get("request_id")
    if not request_id:
        flash("Please select an approved blood request to issue.", "danger")
        return redirect(url_for("blood_issues"))

    user_id = session["user"]["id"]
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Lock the request row to prevent race conditions and duplicate issues
        cursor.execute("SELECT * FROM blood_requests WHERE request_id = %s FOR UPDATE", (request_id,))
        req = cursor.fetchone()

        if not req:
            conn.rollback()
            flash("Blood request record not found.", "danger")
            return redirect(url_for("blood_issues"))

        if req["status"] != "Approved":
            conn.rollback()
            flash(f"Cannot process issue: Request status is '{req['status']}'. Only 'Approved' requests can be issued.", "warning")
            return redirect(url_for("blood_issues"))

        # Verify no prior issue exists for this request
        cursor.execute("SELECT issue_id FROM blood_issues WHERE request_id = %s", (request_id,))
        if cursor.fetchone():
            conn.rollback()
            flash("This request has already been issued! Duplicate fulfillment is prevented.", "danger")
            return redirect(url_for("blood_issues"))

        # 2. Lock inventory row for this blood group
        blood_group = req["blood_group"]
        units_needed = req["units_required"]

        cursor.execute("SELECT available_units FROM inventory WHERE blood_group = %s FOR UPDATE", (blood_group,))
        inv = cursor.fetchone()

        if not inv or inv["available_units"] < units_needed:
            conn.rollback()
            current_avail = inv["available_units"] if inv else 0
            flash(
                f"Insufficient stock for Blood Group {blood_group}! "
                f"Required: {units_needed} unit(s), Available: {current_avail} unit(s). "
                f"Transaction aborted without modifying database.", 
                "danger"
            )
            return redirect(url_for("blood_issues"))

        # 3. Decrement inventory
        cursor.execute("""
            UPDATE inventory 
            SET available_units = available_units - %s 
            WHERE blood_group = %s
        """, (units_needed, blood_group))

        # 4. Insert into blood_issues record
        cursor.execute("""
            INSERT INTO blood_issues (request_id, patient_name, blood_group, units_issued, issue_date, issued_by)
            VALUES (%s, %s, %s, %s, CURRENT_DATE(), %s)
        """, (request_id, req["patient_name"], blood_group, units_needed, user_id))

        # 5. Mark request as Fulfilled
        cursor.execute("UPDATE blood_requests SET status = 'Fulfilled' WHERE request_id = %s", (request_id,))

        # Commit transaction atomically
        conn.commit()
        flash(f"Success! {units_needed} unit(s) of {blood_group} issued to {req['patient_name']} at {req['hospital_name']}.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Database transaction error during issue: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("blood_issues"))

# -------------------------------------------------------------------------
# Reports Route
# -------------------------------------------------------------------------
@app.route("/reports")
@login_required
def reports():
    # 1. Total registered donors (active & total)
    donor_stats = db.query_db("""
        SELECT COUNT(*) AS total_donors,
               SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_donors
        FROM donors
    """, one=True)

    # 2. Aggregate Donations by Blood Group (COUNT & SUM units)
    donations_by_group = db.query_db("""
        SELECT blood_group, 
               COUNT(*) AS donation_count,
               COALESCE(SUM(units_donated), 0) AS total_units_donated
        FROM donations
        WHERE status = 'Accepted'
        GROUP BY blood_group
        ORDER BY FIELD(blood_group, 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
    """)

    # 3. Available Inventory Summary
    inventory_summary = db.query_db("""
        SELECT blood_group, available_units, last_updated
        FROM inventory
        ORDER BY FIELD(blood_group, 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
    """)
    total_inventory_units = sum(item["available_units"] for item in inventory_summary)

    # 4. Request and Issue Performance
    request_stats = db.query_db("""
        SELECT COUNT(*) AS total_requests,
               SUM(CASE WHEN status = 'Fulfilled' THEN 1 ELSE 0 END) AS fulfilled_count,
               SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved_count,
               SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending_count,
               SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) AS rejected_count
        FROM blood_requests
    """, one=True)

    issue_stats = db.query_db("""
        SELECT COUNT(*) AS total_issues,
               COALESCE(SUM(units_issued), 0) AS total_units_issued
        FROM blood_issues
    """, one=True)

    # 5. Monthly Donation Summary using GROUP BY & DATE_FORMAT
    monthly_donations = db.query_db("""
        SELECT DATE_FORMAT(donation_date, '%Y-%m') AS donation_month,
               COUNT(*) AS donation_count,
               COALESCE(SUM(units_donated), 0) AS units_donated
        FROM donations
        WHERE status = 'Accepted'
        GROUP BY DATE_FORMAT(donation_date, '%Y-%m')
        ORDER BY donation_month DESC
        LIMIT 6
    """)

    # Prepare labels and values for Chart.js bar chart
    canonical_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    units_dict = {row["blood_group"]: row["total_units_donated"] for row in donations_by_group}
    chart_labels = canonical_groups
    chart_data = [units_dict.get(g, 0) for g in canonical_groups]

    return render_template(
        "reports.html",
        donor_stats=donor_stats,
        donations_by_group=donations_by_group,
        inventory_summary=inventory_summary,
        total_inventory_units=total_inventory_units,
        request_stats=request_stats,
        issue_stats=issue_stats,
        monthly_donations=monthly_donations,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

# -------------------------------------------------------------------------
# User Management (Admin Only)
# -------------------------------------------------------------------------
@app.route("/users")
@admin_required
def manage_users():
    user_list = db.query_db("SELECT user_id, username, full_name, email, role, is_active, created_at FROM users ORDER BY user_id ASC")
    return render_template("users.html", users=user_list)

@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    if not verify_csrf():
        return redirect(url_for("manage_users"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role", "staff").strip()

    if not username or not password or not full_name or not email or role not in ["admin", "staff"]:
        flash("All fields are required and role must be Admin or Staff.", "danger")
        return redirect(url_for("manage_users"))

    # Check for existing username or email
    existing = db.query_db("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
    if existing:
        flash("Username or Email already registered.", "danger")
        return redirect(url_for("manage_users"))

    password_hash = generate_password_hash(password)
    db.execute_db("""
        INSERT INTO users (username, password_hash, full_name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, 1)
    """, (username, password_hash, full_name, email, role))

    flash(f"User account '{username}' ({role}) created successfully.", "success")
    return redirect(url_for("manage_users"))

@app.route("/users/toggle/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user(user_id):
    if not verify_csrf():
        return redirect(url_for("manage_users"))

    if user_id == session["user"]["id"]:
        flash("You cannot deactivate your own active admin account.", "warning")
        return redirect(url_for("manage_users"))

    target = db.query_db("SELECT is_active, username FROM users WHERE user_id = %s", (user_id,), one=True)
    if not target:
        flash("User not found.", "danger")
        return redirect(url_for("manage_users"))

    new_status = 0 if target["is_active"] else 1
    db.execute_db("UPDATE users SET is_active = %s WHERE user_id = %s", (new_status, user_id))
    action_label = "deactivated" if new_status == 0 else "reactivated"
    flash(f"User '{target['username']}' has been {action_label}.", "info")
    return redirect(url_for("manage_users"))

# -------------------------------------------------------------------------
# Application Entry Point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"Blood Bank Management System running at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
