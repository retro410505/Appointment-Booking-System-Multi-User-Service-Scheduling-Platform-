-- ==============================================================================
-- Appointment Booking System - Database Schema
-- ==============================================================================
-- This script defines the SQLite relational schema for the Appointment Booking
-- System. It sets up 5 primary tables: users, provider_profiles, services,
-- appointment_slots, and bookings, enforcing foreign key relationships and
-- integrity constraints.
-- ==============================================================================

-- Enable SQLite foreign key constraint enforcement
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------------------------
-- 1. Users Table
-- ------------------------------------------------------------------------------
-- Stores authentication credentials, identity, and role-based access status.
-- Supports three user roles: 'admin', 'provider', and 'customer'.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'provider', 'customer')),
    is_approved INTEGER NOT NULL DEFAULT 1,  -- 0=pending approval (providers), 1=approved
    is_active INTEGER NOT NULL DEFAULT 1,    -- 0=deactivated/blocked, 1=active
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. Provider Profiles Table
-- ------------------------------------------------------------------------------
-- Extended professional information for service providers.
-- One-to-one relationship with the users table where role = 'provider'.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    category TEXT NOT NULL,                  -- e.g., 'Education', 'IT Support', 'Consultancy'
    bio TEXT DEFAULT '',
    experience TEXT DEFAULT '',
    qualifications TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 3. Services Table
-- ------------------------------------------------------------------------------
-- Offerings created and managed by service providers.
-- One provider can offer multiple distinct services.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT DEFAULT '',
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    price REAL NOT NULL DEFAULT 0.0,
    is_active INTEGER NOT NULL DEFAULT 1,    -- 0=temporarily inactive, 1=available
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 4. Appointment Slots Table
-- ------------------------------------------------------------------------------
-- Time windows published by service providers for appointment availability.
-- Enforces uniqueness per provider, date, and start time to prevent duplicate slots.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointment_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    slot_date TEXT NOT NULL,                 -- Format: YYYY-MM-DD
    start_time TEXT NOT NULL,                -- Format: HH:MM
    end_time TEXT NOT NULL,                  -- Format: HH:MM
    is_booked INTEGER NOT NULL DEFAULT 0,    -- 0=available, 1=booked
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(provider_id, slot_date, start_time)
);

-- ------------------------------------------------------------------------------
-- 5. Bookings Table
-- ------------------------------------------------------------------------------
-- Appointment reservations linking customer, provider, service, and chosen slot.
-- Tracks the lifecycle of a booking from 'pending' to 'completed' or 'cancelled'.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL UNIQUE,         -- Prevents multiple bookings for the same slot
    notes TEXT DEFAULT '',                   -- Customer request notes or reason for visit
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'rejected', 'cancelled', 'completed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES appointment_slots(id) ON DELETE CASCADE
);
