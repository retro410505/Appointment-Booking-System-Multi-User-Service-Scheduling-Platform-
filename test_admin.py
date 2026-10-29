"""
==============================================================================
Appointment Booking System - Admin Tests
==============================================================================
Automated unit tests to verify admin-only functionality including provider
approval, user deactivation, and service listing management.
==============================================================================
"""

import os
import unittest
import tempfile
from app import create_app
import db
from models import User
from werkzeug.security import generate_password_hash

class AdminTestCase(unittest.TestCase):
    """Test suite for Admin features."""

    def setUp(self):
        """Set up test database and test Flask client."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret',
            'WTF_CSRF_ENABLED': False
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.init_db(self.db_path)
            # Create admin
            conn = db.get_db()
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, 1, 1)",
                ("Admin", "admin@example.com", generate_password_hash("admin123"), "admin")
            )
            # Create pending provider
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, 0, 1)",
                ("Prov", "prov@example.com", generate_password_hash("password123"), "provider")
            )
            # Create customer
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, 1, 1)",
                ("Cust", "cust@example.com", generate_password_hash("password123"), "customer")
            )
            conn.commit()

        # Login as admin
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'admin123'})

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_approve_provider(self):
        """Test admin approving a provider."""
        with self.app.app_context():
            prov = User.get_by_email("prov@example.com")
            self.assertFalse(prov.is_approved)

        self.client.post(f'/admin/provider/{prov.id}/approve', follow_redirects=True)

        with self.app.app_context():
            prov = User.get_by_email("prov@example.com")
            self.assertTrue(prov.is_approved)

    def test_deactivate_and_activate_customer(self):
        """Test admin deactivating a customer and reactivating them."""
        with self.app.app_context():
            cust = User.get_by_email("cust@example.com")
            self.assertTrue(cust.is_active)

        # Deactivate
        self.client.post(f'/admin/user/{cust.id}/toggle-active', follow_redirects=True)

        # Logout admin
        self.client.get('/logout')

        # Try to login as customer
        response = self.client.post('/login', data={'email': 'cust@example.com', 'password': 'password123'}, follow_redirects=True)
        self.assertIn(b'Account deactivated.', response.data)

        # Login as admin again
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'admin123'})

        # Reactivate
        self.client.post(f'/admin/user/{cust.id}/toggle-active', follow_redirects=True)

        # Logout admin
        self.client.get('/logout')

        # Try to login as customer again
        response = self.client.post('/login', data={'email': 'cust@example.com', 'password': 'password123'}, follow_redirects=True)
        self.assertIn(b'Customer Dashboard', response.data)

if __name__ == '__main__':
    unittest.main()
