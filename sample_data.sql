-- =======================================================================
-- BLOOD BANK DONATION AND ISSUE MANAGEMENT SYSTEM
-- Sample Data Script (sample_data.sql)
-- Consistent relational records with verified inventory totals
-- =======================================================================

USE blood_bank_db;

-- Clear any existing records in reverse dependency order
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE blood_issues;
TRUNCATE TABLE blood_requests;
TRUNCATE TABLE donations;
TRUNCATE TABLE inventory;
TRUNCATE TABLE donors;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------
-- 1. Insert Initial Users
-- Password for admin: Admin@123
-- Password for staff accounts: Staff@123
-- (Hashed using Werkzeug scrypt algorithm)
-- -----------------------------------------------------------------------
INSERT INTO users (user_id, username, password_hash, full_name, email, role, is_active) VALUES
(1, 'admin', 'scrypt:32768:8:1$5G1DTkp0aLvlM65c$3221d04d5c92dab4b432479351f0f8ccfca49387354d2854840bbe4f13f902b027038c3e2eb6b55b73c9c3050c7ba187ce997fe566c6e6d1030add032387c821', 'Dr. Arvind Sharma (Chief Medical Officer)', 'admin@bloodbank.org', 'admin', 1),
(2, 'staff_rahul', 'scrypt:32768:8:1$WrLCe22OFthBWo2R$0f7ed0a352c17c76851c03992eb14391b6add7cdc9c6384b589138e05a699db08201c7d7bb399c7baf3206904688a193b174447ff9056d072094b7b36102f859', 'Rahul Verma (Lab Officer)', 'rahul@bloodbank.org', 'staff', 1),
(3, 'staff_priya', 'scrypt:32768:8:1$WrLCe22OFthBWo2R$0f7ed0a352c17c76851c03992eb14391b6add7cdc9c6384b589138e05a699db08201c7d7bb399c7baf3206904688a193b174447ff9056d072094b7b36102f859', 'Priya Deshmukh (Donation Coordinator)', 'priya@bloodbank.org', 'staff', 1),
(4, 'staff_amit', 'scrypt:32768:8:1$WrLCe22OFthBWo2R$0f7ed0a352c17c76851c03992eb14391b6add7cdc9c6384b589138e05a699db08201c7d7bb399c7baf3206904688a193b174447ff9056d072094b7b36102f859', 'Amit Patel (Inventory Specialist)', 'amit@bloodbank.org', 'staff', 1);

-- -----------------------------------------------------------------------
-- 2. Insert Donors (Minimum 8 donors covering groups)
-- -----------------------------------------------------------------------
INSERT INTO donors (donor_id, full_name, age, gender, blood_group, phone, email, address, is_active, registration_date) VALUES
(1, 'Ramesh Chandra', 28, 'Male', 'A+', '9876543210', 'ramesh.c@example.com', 'Sector 14, Navi Mumbai', 1, '2026-08-10'),
(2, 'Sunita Rao', 34, 'Female', 'A-', '9876543211', 'sunita.rao@example.com', 'Bandra West, Mumbai', 1, '2026-08-15'),
(3, 'Vikramaditya Sen', 24, 'Male', 'B+', '9876543212', 'vikram.sen@example.com', 'Koregaon Park, Pune', 1, '2026-08-20'),
(4, 'Ananya Kulkarni', 30, 'Female', 'B-', '9876543213', 'ananya.k@example.com', 'Shivajinagar, Pune', 1, '2026-08-25'),
(5, 'Rajesh Gupta', 45, 'Male', 'A+', '9876543214', 'rajesh.gupta@example.com', 'Andheri East, Mumbai', 1, '2026-09-01'),
(6, 'Sneha Iyer', 29, 'Female', 'AB+', '9876543215', 'sneha.iyer@example.com', 'Indiranagar, Bengaluru', 1, '2026-09-05'),
(7, 'Mohammad Farooq', 38, 'Male', 'AB-', '9876543216', 'farooq.m@example.com', 'Camp, Pune', 1, '2026-09-10'),
(8, 'Pooja Nair', 26, 'Female', 'O+', '9876543217', 'pooja.nair@example.com', 'Whitefield, Bengaluru', 1, '2026-09-12'),
(9, 'Devendra Joshi', 32, 'Male', 'O-', '9876543218', 'devendra.j@example.com', 'Thane West, Mumbai', 1, '2026-09-15');

-- -----------------------------------------------------------------------
-- 3. Insert Donations
-- Statuses: Accepted (adds to stock), Pending, Rejected
-- -----------------------------------------------------------------------
INSERT INTO donations (donation_id, donor_id, blood_group, donation_date, units_donated, status, recorded_by, inventory_updated, remarks) VALUES
-- A+ (Total Accepted = 2 + 2 + 1 = 5 units)
(1, 1, 'A+', '2026-09-18', 2, 'Accepted', 2, 1, 'Screened negative for infections. Cleared for storage.'),
(2, 1, 'A+', '2026-10-01', 2, 'Accepted', 2, 1, 'Routine quarterly donation. Good hemoglobin.'),
(3, 5, 'A+', '2026-10-05', 1, 'Accepted', 3, 1, 'Voluntary blood drive donation.'),

-- A- (Total Accepted = 4 units)
(4, 2, 'A-', '2026-09-20', 4, 'Accepted', 2, 1, 'Rare Rh negative group donor. Cleared.'),

-- B+ (Total Accepted = 3 + 3 = 6 units)
(5, 3, 'B+', '2026-09-22', 3, 'Accepted', 3, 1, 'Good vitals, healthy recovery.'),
(6, 3, 'B+', '2026-10-02', 3, 'Accepted', 3, 1, 'College camp donation.'),

-- B- (Total Accepted = 3 units)
(7, 4, 'B-', '2026-09-25', 3, 'Accepted', 2, 1, 'Eligible and safe for whole blood storage.'),

-- AB+ (Total Accepted = 4 units)
(8, 6, 'AB+', '2026-09-28', 4, 'Accepted', 4, 1, 'Universal recipient group units verified.'),

-- AB- (Total Accepted = 2 units)
(9, 7, 'AB-', '2026-10-02', 2, 'Accepted', 4, 1, 'Critically rare group. Stored in reserve.'),

-- O+ (Total Accepted = 5 + 4 = 9 units)
(10, 8, 'O+', '2026-09-15', 5, 'Accepted', 2, 1, 'High demand group. Verified.'),
(11, 8, 'O+', '2026-10-04', 4, 'Accepted', 3, 1, 'Hospital blood camp donation.'),

-- O- (Total Accepted = 4 units)
(12, 9, 'O-', '2026-09-30', 4, 'Accepted', 2, 1, 'Universal red cell donor. Cleared.'),

-- Pending and Rejected donations (Do NOT affect inventory stock)
(13, 1, 'A+', '2026-10-10', 1, 'Pending', 2, 0, 'Under serological testing, awaiting ELISA report.'),
(14, 3, 'B+', '2026-10-11', 1, 'Rejected', 3, 0, 'Donor had mild fever and sub-threshold hemoglobin (11.8 g/dL).');

-- -----------------------------------------------------------------------
-- 4. Insert Blood Requests
-- Statuses: Fulfilled, Approved, Pending, Rejected
-- -----------------------------------------------------------------------
INSERT INTO blood_requests (request_id, patient_name, hospital_name, blood_group, units_required, request_date, status, created_by) VALUES
(1, 'Tanvi Deshmukh', 'Lilavati Hospital & Research Centre', 'A+', 2, '2026-10-02', 'Fulfilled', 2),
(2, 'Karan Malhotra', 'Ruby Hall Clinic Pune', 'A-', 2, '2026-10-04', 'Fulfilled', 2),
(3, 'Sunil Gavaskar', 'Fortis Hospital Mulund', 'B+', 1, '2026-10-06', 'Fulfilled', 3),
(4, 'Meera Sen', 'Manipal Hospital Bengaluru', 'AB+', 1, '2026-10-07', 'Fulfilled', 4),
(5, 'Sanjay Jadhav', 'KEM Hospital Mumbai', 'O+', 3, '2026-10-08', 'Fulfilled', 2),
(6, 'Rohan Mehra', 'Apollo Hospital Navi Mumbai', 'O-', 1, '2026-10-09', 'Approved', 3),
(7, 'Geeta Kapoor', 'Sahyadri Specialty Hospital Pune', 'O+', 2, '2026-10-10', 'Approved', 2),
(8, 'Harish Trivedi', 'Hinduja Healthcare Surgical', 'AB+', 2, '2026-10-10', 'Rejected', 1),
(9, 'Preeti Verma', 'Jehangir Hospital Pune', 'B-', 1, '2026-10-11', 'Pending', 3);

-- -----------------------------------------------------------------------
-- 5. Insert Blood Issues
-- Exactly matches Fulfilled requests!
-- -----------------------------------------------------------------------
INSERT INTO blood_issues (issue_id, request_id, patient_name, blood_group, units_issued, issue_date, issued_by) VALUES
(1, 1, 'Tanvi Deshmukh', 'A+', 2, '2026-10-03', 1),
(2, 2, 'Karan Malhotra', 'A-', 2, '2026-10-05', 2),
(3, 3, 'Sunil Gavaskar', 'B+', 1, '2026-10-07', 3),
(4, 4, 'Meera Sen', 'AB+', 1, '2026-10-08', 4),
(5, 5, 'Sanjay Jadhav', 'O+', 3, '2026-10-09', 1);

-- -----------------------------------------------------------------------
-- 6. Insert Canonical Inventory (8 Blood Groups)
-- Formula: Available = SUM(Accepted Donations) - SUM(Blood Issues)
-- A+:  5 donated - 2 issued = 3 available (Low Stock alert <= 5)
-- A-:  4 donated - 2 issued = 2 available (Low Stock alert <= 5)
-- B+:  6 donated - 1 issued = 5 available (Low Stock alert <= 5)
-- B-:  3 donated - 0 issued = 3 available (Low Stock alert <= 5)
-- AB+: 4 donated - 1 issued = 3 available (Low Stock alert <= 5)
-- AB-: 2 donated - 0 issued = 2 available (Low Stock alert <= 5)
-- O+:  9 donated - 3 issued = 6 available (Normal Stock > 5)
-- O-:  4 donated - 0 issued = 4 available (Low Stock alert <= 5)
-- Total Units: 37 accepted - 9 issued = 28 available units.
-- -----------------------------------------------------------------------
INSERT INTO inventory (blood_group, available_units, last_updated) VALUES
('A+', 3, NOW()),
('A-', 2, NOW()),
('B+', 5, NOW()),
('B-', 3, NOW()),
('AB+', 3, NOW()),
('AB-', 2, NOW()),
('O+', 6, NOW()),
('O-', 4, NOW());
