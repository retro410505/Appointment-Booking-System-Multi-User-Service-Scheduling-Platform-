"""
==============================================================================
Appointment Booking System - Admin Seed Script
==============================================================================
Seeds the initial administrator account into the database if one does not
already exist. The administrator has full oversight over users, services,
and appointment schedules.
==============================================================================
"""

import sys
from werkzeug.security import generate_password_hash
import db

# Administrator account default credentials
ADMIN_NAME = "System Administrator"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "admin"


def seed_admin_user():
    """
    Ensure the default administrator user exists in the database.

    Initializes the database schema if tables have not yet been created,
    checks for the existence of an account with the designated admin email,
    and creates a new hashed credential record if absent.

    Returns:
        bool: True if a new admin was created, False if already present.
    """
    # Ensure database tables exist prior to query/insert
    db.init_db()

    conn = db.get_db()
    cursor = conn.cursor()

    try:
        # Check whether an administrator account with the designated email already exists
        cursor.execute("SELECT id, email FROM users WHERE email = ?", (ADMIN_EMAIL,))
        existing_admin = cursor.fetchone()

        if existing_admin:
            print(f"[INFO] Admin user '{ADMIN_EMAIL}' already exists (User ID: {existing_admin['id']}). Skipping creation.")
            return False

        # Generate a secure one-way cryptographic hash of the default password
        password_hash = generate_password_hash(ADMIN_PASSWORD)

        # Insert administrator user record with pre-approved and active status
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash, role, is_approved, is_active)
            VALUES (?, ?, ?, ?, 1, 1)
            """,
            (ADMIN_NAME, ADMIN_EMAIL, password_hash, ADMIN_ROLE)
        )
        conn.commit()

        print(f"[SUCCESS] Admin user created successfully.")
        print(f"          Email:    {ADMIN_EMAIL}")
        print(f"          Role:     {ADMIN_ROLE}")
        print(f"          Status:   Active & Approved")
        return True

    finally:
        conn.close()


# ==============================================================================
# Script Execution Entry Point
# ==============================================================================
if __name__ == '__main__':
    try:
        seed_admin_user()
        sys.exit(0)
    except Exception as exc:
        print(f"[ERROR] Failed to seed admin user: {exc}", file=sys.stderr)
        sys.exit(1)
