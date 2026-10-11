# BLOOD BANK DONATION AND ISSUE MANAGEMENT SYSTEM

[![GitHub Repository](https://img.shields.io/badge/GitHub-Andrewdevasani123%2FDBMS__PBL-blue?logo=github)](https://github.com/Andrewdevasani123/DBMS_PBL.git)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed%20(100%25)-success)](https://github.com/Andrewdevasani123/DBMS_PBL.git)

| Field | Details |
|---|---|
| **Student** | Andrew Devasani |
| **Roll Number** | 25WU0102067 |
| **Guide / Faculty** | Prof. Sahiti |
| **Programme** | B.Tech Computer Science & Engineering |
| **Subject** | Database Management Systems (DBMS) — PBL |
| **Repository** | [https://github.com/Andrewdevasani123/DBMS_PBL.git](https://github.com/Andrewdevasani123/DBMS_PBL.git) |

> **Academic Coursework Project:** B.Tech Computer Science & Engineering (DBMS Assignment / PBL)  
> **Clinical Disclaimer:** This application is an educational prototype designed to demonstrate relational database modeling, ACID transactions, and full-stack integration. It is not certified for clinical patient diagnosis or actual transfusion decision-making.

---

## 1. Project Overview & Architecture

The **Blood Bank Donation and Issue Management System** is a complete, modern, full-stack hospital administration dashboard that connects a clean frontend, a Python Flask backend, and a relational MySQL database.

### Key Capabilities:
- **Two User Roles:** Admin (complete privileges, staff account management, approvals) and Staff (donor registration, donations, requisitions, issue dispatch).
- **Relational Integrity:** Implements Third Normal Form (3NF) relational design across 6 core tables with Primary Keys, Foreign Keys (`CASCADE` / `RESTRICT`), and `CHECK` constraints.
- **Atomic Stock Management:** Uses MySQL transactions with row-level locks (`SELECT ... FOR UPDATE`) to guarantee that blood issue records and inventory deductions happen atomically without race conditions or negative balances.
- **Real-Time Data Integration:** All dashboard statistics, 8-group inventory grids, recent activity tables, and reports are dynamically computed from live MySQL data.

---

## 2. Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6)
- **Backend:** Python 3.10+ / Flask 3.1
- **Database:** MySQL 8.0+
- **MySQL Driver:** `mysql-connector-python`
- **Template Engine:** Jinja2
- **Icons:** Lucide Icons (CDN)
- **Charts:** Chart.js (CDN)
- **Authentication:** Flask Server Sessions + Werkzeug `scrypt` cryptographic password hashing

---

## 3. Project Folder Structure

```
blood_bank_project/
├── app.py                     # Main Flask application with routes and controllers
├── db.py                      # MySQL connection manager & parameterized query runner
├── requirements.txt           # Python dependency specifications
├── .env.example               # Environment variables configuration template
├── .env                       # Active local credentials configuration
├── README.md                  # Comprehensive setup and demonstration documentation
├── schema.sql                 # 3NF database schema with constraints & indexes
├── sample_data.sql            # Consistent demo data balancing donations, issues & stock
├── dbms_queries.sql           # DBMS evaluation queries with in-depth academic explanations
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base hospital layout with sidebar & topbar
│   ├── login.html             # Clean login card with 1-click credential filler
│   ├── dashboard.html         # Live KPI cards, 8-group grid & low-stock alerts
│   ├── donors.html            # Donor registry, search, edit & deactivation
│   ├── donations.html         # Donation recording & pending lab approval
│   ├── inventory.html         # Live inventory stock & prototype disclaimer
│   ├── requests.html          # Hospital requisition management & stock checks
│   ├── issues.html            # Atomic blood issuing with row-level locking
│   ├── reports.html           # Aggregate metrics & Chart.js donations breakdown
│   └── users.html             # Admin-only staff account administration
├── static/
│   ├── css/
│   │   └── style.css          # Modern hospital design system (#DC3545 / #F8F9FA)
│   └── js/
│       └── main.js            # Modals, live clock & form event handlers
├── docs/
│   ├── er_diagram.md          # Mermaid ER diagram & 1NF/2NF/3NF normalization proofs
│   └── database_explanation.md# Detailed table-by-table schema data dictionary
└── tests/
    └── test_system.py         # Automated pytest suite covering 12 test requirements
```

---

## 4. Prerequisites & Required Software

Ensure the following software is installed on your Windows machine:
1. **Git** (for version control and repository cloning)
2. **Python 3.10+** (Python 3.12 recommended)
3. **MySQL Server 8.0+** (or MySQL Community Server / XAMPP with MySQL)
4. **MySQL Workbench 8.0+** (recommended for visual table inspection)
5. **Google Antigravity IDE** or **Visual Studio Code**

---

## 5. Step-by-Step Installation & Setup (Windows)

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Andrewdevasani123/DBMS_PBL.git
cd DBMS_PBL\blood_bank_project
```

### Step 2: Install Python Dependencies
Install all required Python packages:
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Configure Environment Variables (`.env`)
The `.env` file contains database and session settings:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=1234
DB_NAME=blood_bank_db

SECRET_KEY=blood_bank_btech_secret_key_2026
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
LOW_STOCK_THRESHOLD=5
```
*(Adjust `DB_PASSWORD` to match your local MySQL root password).*

### Step 4: Import Database Schema and Sample Records
Run the following commands using the MySQL CLI, or open and execute them in **MySQL Workbench**:
```powershell
# Import Schema (Creates database and tables)
mysql -u root -p1234 -e "source schema.sql"

# Import Sample Data (Populates users, donors, donations, requests, inventory)
mysql -u root -p1234 blood_bank_db -e "source sample_data.sql"
```

---

## 6. Running the Flask Application

Start the Flask development server:
```powershell
python app.py
```

Output:
```
Blood Bank Management System running at http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Open your web browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)** (or `http://127.0.0.1:5000`)

---

## 7. Demo Login Credentials

The system comes pre-configured with active demo accounts. On the login page, you can either type these credentials or click the **Auto Fill** buttons:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Full dashboard, inventory, approvals, dispatch, reports, staff account management |
| **Staff** | `staff_rahul` | `Staff@123` | Register donors, record donations, view inventory, create requests, process issues |
| **Staff** | `staff_priya` | `Staff@123` | Donation coordination & intake |
| **Staff** | `staff_amit` | `Staff@123` | Inventory specialist |

---

## 8. 5–8 Minute College Presentation / Viva Walkthrough

When presenting this project to your college professor or external evaluator, follow this structured 6-step walkthrough:

1. **Login & Role Access (1 min):**
   - Navigate to `http://localhost:5000`.
   - Click **Auto Fill** for `admin` and sign in.
   - Point out the clean hospital administration layout, red medical branding, and role badge in the topbar.
2. **Dashboard & Live Statistics (1 min):**
   - Highlight the 4 summary cards (Active Donors, Total Donations, Available Blood Units, Total Issues Fulfilled).
   - Point to the **Low Blood Stock Alert banner** and the 8-card inventory grid showing live stock for A+, A-, B+, B-, AB+, AB-, O+, O-.
   - Emphasize that all figures are dynamically queried from MySQL tables (`SELECT COUNT(*)`, `SUM(available_units)`).
3. **Donor Management (1 min):**
   - Click **Donor Management** in the sidebar.
   - Click **Register New Donor** and submit a new donor (e.g., age 24, blood group B+).
   - Demonstrate searching by name and filtering by blood group.
   - Demonstrate deactivating a donor: highlight that historical donation records remain safely preserved in the database.
4. **Blood Donation & Stock Increment (1.5 min):**
   - Click **Blood Donations**.
   - Click **Record New Donation**: select an active donor (blood group is auto-fetched), choose **Accepted**, and save.
   - Switch to **Blood Inventory** and demonstrate that the blood group unit count increased immediately!
5. **Hospital Request & Atomic Blood Issue (2 min):**
   - Click **Blood Requests**: note the live comparison between units demanded and available bank stock.
   - Approve a pending request.
   - Click **Blood Issues**: show the row-locking atomic issue workflow.
   - Click **Issue Blood**: the transaction deducts stock, creates an issue audit log, and marks the request `Fulfilled`.
   - Point out the error prevention: show that if a request requires more units than available, the system rolls back without modifying inventory!
6. **Reports & SQL Aggregates (1 min):**
   - Click **Reports** to display the Chart.js visual distribution of donations by blood group, `GROUP BY` tables, and monthly trends.
   - Open `dbms_queries.sql` in VS Code to explain joins, transactions, and normalization.

---

## 9. Verifying Records Using MySQL Workbench

To inspect the live MySQL database in MySQL Workbench:
1. Open **MySQL Workbench**.
2. Connect to your local MySQL instance (`localhost:3306`, user: `root`).
3. In the left *Navigator* panel under *SCHEMAS*, expand `blood_bank_db`.
4. Right-click any table (`inventory`, `donors`, `blood_issues`) and select **Select Rows - Limit 1000**.
5. Execute the inventory verification query:
   ```sql
   SELECT blood_group, available_units, last_updated 
   FROM blood_bank_db.inventory;
   ```
   Notice that the total available units matches `SUM(Accepted Donations) - SUM(Units Issued)`!

---

## 10. Running the Automated Test Suite

A complete test suite covering all 12 evaluation criteria is provided in `tests/test_system.py`.

Run the tests via pytest:
```powershell
python -m pytest tests/test_system.py -v
```

Expected output:
```
============================= test session starts =============================
tests/test_system.py::test_01_admin_login PASSED                         [  9%]
tests/test_system.py::test_02_staff_login PASSED                         [ 18%]
tests/test_system.py::test_03_unauthorized_access PASSED                 [ 27%]
tests/test_system.py::test_04_donor_registration PASSED                  [ 36%]
tests/test_system.py::test_05_donation_recording PASSED                  [ 45%]
tests/test_system.py::test_06_inventory_increase PASSED                  [ 54%]
tests/test_system.py::test_07_blood_request_creation PASSED              [ 63%]
tests/test_system.py::test_08_and_09_blood_issue_and_inventory_decrease PASSED [ 72%]
tests/test_system.py::test_10_insufficient_inventory PASSED              [ 81%]
tests/test_system.py::test_11_duplicate_issue_prevention PASSED          [ 90%]
tests/test_system.py::test_12_invalid_form_inputs PASSED                 [100%]

============================= 11 passed in 18.68s =============================
```

---

## 11. Troubleshooting & Frequently Asked Questions (FAQ)

### Q1: `Access denied for user 'root'@'localhost'`
- **Fix:** Update `DB_PASSWORD` in `blood_bank_project/.env` with your actual MySQL root password.

### Q2: `Can't connect to MySQL server on 'localhost:3306'`
- **Fix:** Verify that the MySQL service is running. On Windows, press `Win + R`, type `services.msc`, locate `MySQL80` (or `MySQL`), right-click and select **Start**.

### Q3: `Port 5000 is already in use`
- **Fix:** Change `PORT=5001` inside `.env`, then restart `python app.py`.

### Q4: How do I reset the database to sample records?
- **Fix:** Run:
  ```powershell
  mysql -u root -p1234 blood_bank_db -e "source schema.sql"; mysql -u root -p1234 blood_bank_db -e "source sample_data.sql"
  ```
