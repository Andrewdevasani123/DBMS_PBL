-- =======================================================================
-- BLOOD BANK DONATION AND ISSUE MANAGEMENT SYSTEM
-- Database Schema Definition (schema.sql)
-- Target RDBMS: MySQL 8.0+
-- Design Standard: Third Normal Form (3NF)
-- =======================================================================

CREATE DATABASE IF NOT EXISTS blood_bank_db 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE blood_bank_db;

-- -----------------------------------------------------------------------
-- 1. Table: users
-- Purpose: System authentication and role-based access (Admin, Staff)
-- -----------------------------------------------------------------------
DROP TABLE IF EXISTS blood_issues;
DROP TABLE IF EXISTS blood_requests;
DROP TABLE IF EXISTS donations;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS donors;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    role ENUM('admin', 'staff') NOT NULL DEFAULT 'staff',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- 2. Table: donors
-- Purpose: Registry of prospective and active blood donors
-- -----------------------------------------------------------------------
CREATE TABLE donors (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NULL,
    address VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    registration_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_donor_age CHECK (age >= 18 AND age <= 65)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- 3. Table: inventory
-- Purpose: Real-time available units per blood group (Educational prototype)
-- Maintains exactly 8 canonical rows, one for each blood group.
-- -----------------------------------------------------------------------
CREATE TABLE inventory (
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') PRIMARY KEY,
    available_units INT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_inventory_non_negative CHECK (available_units >= 0)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- 4. Table: donations
-- Purpose: Transactional log of blood donations provided by registered donors
-- -----------------------------------------------------------------------
CREATE TABLE donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    donation_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    units_donated INT NOT NULL DEFAULT 1,
    status ENUM('Pending', 'Accepted', 'Rejected') NOT NULL DEFAULT 'Pending',
    recorded_by INT NOT NULL,
    inventory_updated BOOLEAN NOT NULL DEFAULT FALSE,
    remarks VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_donation_units CHECK (units_donated > 0),
    CONSTRAINT fk_donations_donor FOREIGN KEY (donor_id) 
        REFERENCES donors(donor_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT,
    CONSTRAINT fk_donations_user FOREIGN KEY (recorded_by) 
        REFERENCES users(user_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- 5. Table: blood_requests
-- Purpose: Requests submitted by hospitals/patients for blood units
-- -----------------------------------------------------------------------
CREATE TABLE blood_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    hospital_name VARCHAR(150) NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    units_required INT NOT NULL,
    request_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('Pending', 'Approved', 'Rejected', 'Fulfilled') NOT NULL DEFAULT 'Pending',
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_request_units CHECK (units_required > 0),
    CONSTRAINT fk_requests_user FOREIGN KEY (created_by) 
        REFERENCES users(user_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- 6. Table: blood_issues
-- Purpose: Record of blood units formally issued against approved requests
-- Note: UNIQUE(request_id) guarantees that one request cannot be fulfilled multiple times.
-- -----------------------------------------------------------------------
CREATE TABLE blood_issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL UNIQUE,
    patient_name VARCHAR(100) NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    units_issued INT NOT NULL,
    issue_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    issued_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_issue_units CHECK (units_issued > 0),
    CONSTRAINT fk_issues_request FOREIGN KEY (request_id) 
        REFERENCES blood_requests(request_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT,
    CONSTRAINT fk_issues_user FOREIGN KEY (issued_by) 
        REFERENCES users(user_id) 
        ON UPDATE CASCADE 
        ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------
-- INDEXES FOR COMMONLY SEARCHED AND FILTERED FIELDS
-- -----------------------------------------------------------------------
CREATE INDEX idx_donors_search ON donors (full_name, blood_group, is_active);
CREATE INDEX idx_donations_status ON donations (status, blood_group);
CREATE INDEX idx_donations_donor ON donations (donor_id);
CREATE INDEX idx_requests_status ON blood_requests (status, blood_group);
CREATE INDEX idx_issues_date ON blood_issues (issue_date);
