# Appointment Booking System

## Project Overview
The Appointment Booking System is a web application built with Python (Flask) and SQLite. It connects customers with service providers (tutors, consultants, technicians) and provides an administrative interface to oversee users and bookings.

## Comment Style Guide
Every file in this project must adhere to the following commenting conventions:
1. **File Header**: Every source file begins with a top-level block comment or docstring outlining the file's responsibility, key dependencies, and role in the system.
2. **Section Dividers**: Logical sections within a file (e.g., configuration, helper functions, routes, SQL table definitions, CSS components) are separated by clear banner comments.
3. **Function & Method Docstrings**: Every function and method has a descriptive docstring documenting its purpose, expected arguments, return value, and exceptions where applicable.
4. **Inline Comments**: Explanatory comments should clarify non-obvious business rules, security constraints, and database integrity invariants.
5. **Template & Style Comments**: HTML templates use `<!-- Section -->` or Jinja `{# comment #}` blocks for structural demarcation. CSS and JS files use `/* Section */` block headers.

## Database Tables (5 Tables)
The system uses SQLite with foreign keys enabled (`PRAGMA foreign_keys = ON;`).

1. `users`
   - Primary account table for all actors: Admin, Service Provider, and Customer.
   - Columns: `id`, `name`, `email` (unique), `password_hash`, `role` (admin/provider/customer), `is_approved`, `is_active`, `created_at`.
2. `provider_profiles`
   - Extended professional details specific to Service Providers.
   - Columns: `id`, `user_id` (FK -> users.id, unique), `category`, `bio`, `experience`, `qualifications`, `created_at`, `updated_at`.
3. `services`
   - Services offered by approved Service Providers.
   - Columns: `id`, `provider_id` (FK -> users.id), `name`, `category`, `description`, `duration_minutes`, `price`, `is_active`, `created_at`.
4. `appointment_slots`
   - Calendar availability slots created by Service Providers.
   - Columns: `id`, `provider_id` (FK -> users.id), `slot_date`, `start_time`, `end_time`, `is_booked`, `created_at`.
5. `bookings`
   - Appointment reservations made by Customers.
   - Columns: `id`, `customer_id` (FK -> users.id), `provider_id` (FK -> users.id), `service_id` (FK -> services.id), `slot_id` (FK -> appointment_slots.id, unique), `notes`, `status` (pending/confirmed/rejected/cancelled/completed), `created_at`, `updated_at`.

## Standard Commands
- Install dependencies: `pip install -r requirements.txt` (or `py -m pip install -r requirements.txt`)
- Seed admin user: `python seed_admin.py` (or `py seed_admin.py`)
- Run development server: `python app.py` (or `py app.py`)
