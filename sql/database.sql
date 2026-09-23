CREATE DATABASE IF NOT EXISTS cab_pooling_db;

USE cab_pooling_db;


-- =========================================
-- USERS
-- =========================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('EMPLOYEE', 'ADMIN') NOT NULL DEFAULT 'EMPLOYEE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================
-- EMPLOYEES
-- =========================================

CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    home_latitude DECIMAL(10, 7) NOT NULL,
    home_longitude DECIMAL(10, 7) NOT NULL,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


-- =========================================
-- OFFICES
-- =========================================

CREATE TABLE IF NOT EXISTS offices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    address VARCHAR(255)
);


-- =========================================
-- SHIFTS
-- =========================================

CREATE TABLE IF NOT EXISTS shifts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    office_id INT NOT NULL,
    shift_name VARCHAR(100) NOT NULL,
    start_time TIME NOT NULL,
    max_ride_minutes INT NOT NULL DEFAULT 90,

    FOREIGN KEY (office_id)
        REFERENCES offices(id)
        ON DELETE CASCADE
);


-- =========================================
-- BOOKINGS
-- =========================================

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_id INT NOT NULL,
    booking_date DATE NOT NULL,
    status ENUM('ACTIVE', 'CANCELLED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (employee_id)
        REFERENCES employees(id)
        ON DELETE CASCADE,

    FOREIGN KEY (shift_id)
        REFERENCES shifts(id)
        ON DELETE CASCADE,

    UNIQUE(employee_id, shift_id, booking_date)
);


-- =========================================
-- CABS
-- =========================================

CREATE TABLE IF NOT EXISTS cabs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cab_number VARCHAR(50) NOT NULL UNIQUE,
    capacity INT NOT NULL,
    booking_date DATE NOT NULL,
    shift_id INT NOT NULL,
    status ENUM('ACTIVE', 'CANCELLED') DEFAULT 'ACTIVE',

    FOREIGN KEY (shift_id)
        REFERENCES shifts(id)
        ON DELETE CASCADE
);


-- =========================================
-- CAB MEMBERS
-- =========================================

CREATE TABLE IF NOT EXISTS cab_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cab_id INT NOT NULL,
    booking_id INT NOT NULL,
    pickup_order INT,
    pickup_eta DATETIME,

    FOREIGN KEY (cab_id)
        REFERENCES cabs(id)
        ON DELETE CASCADE,

    FOREIGN KEY (booking_id)
        REFERENCES bookings(id)
        ON DELETE CASCADE,

    UNIQUE(cab_id, booking_id)
);


-- =========================================
-- ROUTES
-- =========================================

CREATE TABLE IF NOT EXISTS routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cab_id INT NOT NULL UNIQUE,
    total_distance_km DECIMAL(10, 2),
    estimated_duration_minutes INT,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cab_id)
        REFERENCES cabs(id)
        ON DELETE CASCADE
);