-- =======================================================================
-- BLOOD BANK DONATION AND ISSUE MANAGEMENT SYSTEM
-- DBMS Academic Evaluation Queries (dbms_queries.sql)
-- Target RDBMS: MySQL 8.0+
-- Comprehensive examples of DDL, DML, Aggregations, Joins, Subqueries & Transactions
-- =======================================================================

USE blood_bank_db;

-- =======================================================================
-- 1. DDL: CREATE (TABLE & INDEX)
-- Purpose: Demonstrates database table and index definition with integrity constraints
-- =======================================================================

-- Example 1.1: CREATE TABLE with Primary Key, Foreign Key, CHECK and ENUM constraints
CREATE TABLE IF NOT EXISTS blood_bank_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    performed_by INT NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_log_user FOREIGN KEY (performed_by) 
        REFERENCES users(user_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Example 1.2: CREATE INDEX for accelerating queries filtering on active donors and blood groups
CREATE INDEX idx_donors_group_active ON donors (blood_group, is_active);


-- =======================================================================
-- 2. DML: INSERT
-- Purpose: Demonstrates adding new entity and transactional records
-- =======================================================================

-- Example 2.1: INSERT into donors
INSERT INTO donors (full_name, age, gender, blood_group, phone, email, address, is_active, registration_date)
VALUES ('Kavita Ramanathan', 27, 'Female', 'O+', '9811223344', 'kavita.r@example.com', 'Koramangala, Bengaluru', 1, CURRENT_DATE());

-- Example 2.2: INSERT into donations
INSERT INTO donations (donor_id, blood_group, donation_date, units_donated, status, recorded_by, inventory_updated, remarks)
VALUES (LAST_INSERT_ID(), 'O+', CURRENT_DATE(), 1, 'Pending', 2, 0, 'Initial health check passed; ELISA awaiting.');


-- =======================================================================
-- 3. DML: UPDATE
-- Purpose: Demonstrates updating state without violating integrity constraints
-- =======================================================================

-- Example 3.1: Updating donation status from 'Pending' to 'Accepted'
UPDATE donations 
SET status = 'Accepted', 
    inventory_updated = 1,
    remarks = 'Screened negative for HIV, HBV, HCV, Syphilis and Malaria.'
WHERE donation_id = 13;

-- Example 3.2: Incrementing available units in inventory corresponding to accepted donation
UPDATE inventory 
SET available_units = available_units + 1 
WHERE blood_group = 'O+';


-- =======================================================================
-- 4. DML: DELETE (Safe Example preserving historical records)
-- Purpose: Demonstrates safe deletion of an unfulfilled test request without breaking foreign keys
-- In a hospital system, historical medical and financial data should never be hard deleted;
-- soft deletes (is_active = 0) or purging uncommitted test records are used.
-- =======================================================================

-- Example 4.1: Safe deletion of an erroneous pending request that was never approved or fulfilled
DELETE FROM blood_requests 
WHERE status = 'Pending' 
  AND request_id = 999; -- Safe condition that does not affect completed issues


-- =======================================================================
-- 5. AT LEAST TEN USEFUL SELECT QUERIES WITH DBMS EXPLANATIONS
-- =======================================================================

-- -----------------------------------------------------------------------
-- Query 5.1: Live Inventory Status with Stock Health Classification (CASE statement)
-- Purpose: Classifies available inventory into safety tiers for clinical dispatchers.
-- -----------------------------------------------------------------------
SELECT 
    blood_group,
    available_units,
    CASE 
        WHEN available_units <= 2 THEN 'CRITICAL - Urgent Drive Required'
        WHEN available_units <= 5 THEN 'LOW STOCK - Organize Reserve'
        ELSE 'SUFFICIENT - Normal Operations'
    END AS stock_health_status,
    last_updated
FROM inventory
ORDER BY FIELD(blood_group, 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-');


-- -----------------------------------------------------------------------
-- Query 5.2: Active Donors by Blood Group with Sorting (WHERE & ORDER BY)
-- Purpose: Quick lookup of contact details for active donors when an emergency arises.
-- -----------------------------------------------------------------------
SELECT 
    donor_id,
    full_name,
    age,
    gender,
    blood_group,
    phone,
    registration_date
FROM donors
WHERE is_active = 1 AND blood_group = 'O-'
ORDER BY full_name ASC;


-- -----------------------------------------------------------------------
-- Query 5.3: Total Units Donated by Each Blood Group (GROUP BY, COUNT, SUM)
-- Purpose: Analyzes community donation trends and identifies groups with low donation rates.
-- -----------------------------------------------------------------------
SELECT 
    blood_group,
    COUNT(donation_id) AS total_donation_sessions,
    SUM(units_donated) AS total_units_received
FROM donations
WHERE status = 'Accepted'
GROUP BY blood_group
ORDER BY total_units_received DESC;


-- -----------------------------------------------------------------------
-- Query 5.4: Detailed Donation Audit Trail (INNER JOIN with multiple parent tables)
-- Purpose: Audit log showing which donor gave blood, units donated, and which staff verified it.
-- -----------------------------------------------------------------------
SELECT 
    d.donation_id,
    dn.full_name AS donor_name,
    dn.phone AS donor_phone,
    d.blood_group,
    d.units_donated,
    d.donation_date,
    d.status,
    u.full_name AS staff_recorded_by
FROM donations d
INNER JOIN donors dn ON d.donor_id = dn.donor_id
INNER JOIN users u ON d.recorded_by = u.user_id
ORDER BY d.donation_id DESC;


-- -----------------------------------------------------------------------
-- Query 5.5: Donors Who Have Never Donated Blood (LEFT JOIN with IS NULL filter)
-- Purpose: Identifies newly registered prospective donors who can be sent blood camp invitations.
-- -----------------------------------------------------------------------
SELECT 
    dn.donor_id,
    dn.full_name,
    dn.blood_group,
    dn.phone,
    dn.registration_date
FROM donors dn
LEFT JOIN donations d ON dn.donor_id = d.donor_id
WHERE d.donation_id IS NULL;


-- -----------------------------------------------------------------------
-- Query 5.6: Blood Requests Waiting for Stock Approval (WHERE & INNER JOIN)
-- Purpose: Displays hospital requests currently pending evaluation alongside live bank stock.
-- -----------------------------------------------------------------------
SELECT 
    r.request_id,
    r.patient_name,
    r.hospital_name,
    r.blood_group,
    r.units_required,
    i.available_units AS live_stock_in_bank,
    r.request_date,
    r.status
FROM blood_requests r
INNER JOIN inventory i ON r.blood_group = i.blood_group
WHERE r.status = 'Pending'
ORDER BY r.request_date ASC;


-- -----------------------------------------------------------------------
-- Query 5.7: Complete Blood Issue Fulfillment Log (INNER JOIN across 3 tables)
-- Purpose: Demonstrates hospital fulfillment trail linking issue, original request, and staff.
-- -----------------------------------------------------------------------
SELECT 
    bi.issue_id,
    bi.request_id,
    bi.patient_name,
    br.hospital_name,
    bi.blood_group,
    bi.units_issued,
    bi.issue_date,
    u.full_name AS authorized_by_officer
FROM blood_issues bi
INNER JOIN blood_requests br ON bi.request_id = br.request_id
INNER JOIN users u ON bi.issued_by = u.user_id
ORDER BY bi.issue_id DESC;


-- -----------------------------------------------------------------------
-- Query 5.8: Subquery Identifying Blood Groups with Inventory Below Average
-- Purpose: Identifies which blood groups have fewer units than the system-wide average.
-- -----------------------------------------------------------------------
SELECT 
    blood_group,
    available_units
FROM inventory
WHERE available_units < (
    SELECT AVG(available_units) 
    FROM inventory
)
ORDER BY available_units ASC;


-- -----------------------------------------------------------------------
-- Query 5.9: High-Volume Blood Donors (GROUP BY with HAVING Clause)
-- Purpose: Recognizes and rewards frequent donors who have completed multiple donations.
-- -----------------------------------------------------------------------
SELECT 
    dn.donor_id,
    dn.full_name,
    dn.blood_group,
    COUNT(d.donation_id) AS accepted_donations_count,
    SUM(d.units_donated) AS total_units_contributed
FROM donors dn
INNER JOIN donations d ON dn.donor_id = d.donor_id
WHERE d.status = 'Accepted'
GROUP BY dn.donor_id, dn.full_name, dn.blood_group
HAVING COUNT(d.donation_id) >= 2
ORDER BY total_units_contributed DESC;


-- -----------------------------------------------------------------------
-- Query 5.10: Monthly Hospital Requisition Volume (DATE_FORMAT, GROUP BY, SUM)
-- Purpose: Trend analysis to forecast peak transfusion demand across calendar months.
-- -----------------------------------------------------------------------
SELECT 
    DATE_FORMAT(request_date, '%Y-%m') AS requisition_month,
    COUNT(request_id) AS total_hospital_requests,
    SUM(units_required) AS total_units_demanded,
    SUM(CASE WHEN status = 'Fulfilled' THEN units_required ELSE 0 END) AS units_fulfilled
FROM blood_requests
GROUP BY DATE_FORMAT(request_date, '%Y-%m')
ORDER BY requisition_month DESC;


-- =======================================================================
-- 6. MYSQL TRANSACTION DEMONSTRATION (START TRANSACTION, COMMIT & ROLLBACK)
-- Purpose: Demonstrates ACID compliance (Atomicity, Consistency, Isolation, Durability)
-- =======================================================================

-- -----------------------------------------------------------------------
-- Scenario 6.1: Successful Blood Issue Transaction (COMMIT)
-- Atomically deducts inventory stock and inserts fulfillment record.
-- -----------------------------------------------------------------------
START TRANSACTION;

-- Step A: Lock inventory row for Blood Group 'A+' to prevent concurrent race conditions
SELECT available_units 
FROM inventory 
WHERE blood_group = 'A+' 
FOR UPDATE;

-- Step B: Deduct 1 unit from inventory
UPDATE inventory 
SET available_units = available_units - 1 
WHERE blood_group = 'A+' AND available_units >= 1;

-- Step C: Record formal blood issue
INSERT INTO blood_issues (request_id, patient_name, blood_group, units_issued, issue_date, issued_by)
VALUES (6, 'Rohan Mehra', 'O-', 1, CURRENT_DATE(), 1);

-- Step D: Update request status to Fulfilled
UPDATE blood_requests 
SET status = 'Fulfilled' 
WHERE request_id = 6;

-- Both inventory update and issue record committed atomically!
COMMIT;


-- -----------------------------------------------------------------------
-- Scenario 6.2: Aborted Transaction Due to Insufficient Stock (ROLLBACK)
-- Demonstrates how ROLLBACK prevents corrupting database state.
-- -----------------------------------------------------------------------
START TRANSACTION;

-- Step A: Inspect inventory for Blood Group 'AB-'
SELECT available_units 
FROM inventory 
WHERE blood_group = 'AB-' 
FOR UPDATE;

-- Step B: Suppose a request asks for 10 units, but only 2 units are available.
-- We test the condition: If available < requested, abort!
-- Since stock is insufficient, the system issues a ROLLBACK:
ROLLBACK;

-- After ROLLBACK, zero changes are written to the database. Inventory remains intact.
