"""
==============================================================================
Appointment Booking System - Auth Tests
==============================================================================
Automated unit tests to verify registration, login, logout, role-based access
protection, and form validation functionality.
==============================================================================
"""

import os
import unittest
import tempfile
from app import create_app
import db
from models import User
from werkzeug.security import generate_password_hash

class AuthTestCase(unittest.TestCase):
    """
    Test suite for checking register, login, logout, role check decorators, etc.
    """

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
            # Create an admin user for testing
            conn = db.get_db()
            conn.execute(
                "INSERT INTO users (name, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, 1, 1)",
                ("Admin", "admin@example.com", generate_password_hash("admin123"), "admin")
            )
            conn.commit()

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_admin_exists(self):
        """Verify the admin exists and is set up correctly in the test suite."""
        with self.app.app_context():
            user = User.get_by_email("admin@example.com")
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "admin")

    def test_customer_registration(self):
        """Test registration of a customer."""
        response = self.client.post('/register/customer', data={
            'name': 'Customer User',
            'email': 'customer@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful. Please login.', response.data)

        with self.app.app_context():
            user = User.get_by_email("customer@example.com")
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'customer')
            self.assertTrue(user.is_approved)

    def test_provider_registration(self):
        """Test registration of a provider (should be unapproved by default)."""
        response = self.client.post('/register/provider', data={
            'name': 'Provider User',
            'email': 'provider@example.com',
            'password': 'password123',
            'category': 'Tutoring',
            'bio': 'Experienced math tutor.',
            'experience': '5 years'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful. Account awaiting admin approval.', response.data)

        with self.app.app_context():
            user = User.get_by_email("provider@example.com")
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'provider')
            self.assertFalse(user.is_approved)

            # Check profile entry
            conn = db.get_db()
            profile = conn.execute("SELECT * FROM provider_profiles WHERE user_id = ?", (user.id,)).fetchone()
            self.assertIsNotNone(profile)
            self.assertEqual(profile['category'], 'Tutoring')

    def test_form_validations(self):
        """Test registration validation error cases (empty fields, bad email, short password)."""
        # Empty fields
        response = self.client.post('/register/customer', data={
            'name': '',
            'email': 'test@test.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'All fields are required.', response.data)

        # Invalid email
        response = self.client.post('/register/customer', data={
            'name': 'Name',
            'email': 'bademail',
            'password': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email address.', response.data)

        # Short password
        response = self.client.post('/register/customer', data={
            'name': 'Name',
            'email': 'good@email.com',
            'password': '123'
        }, follow_redirects=True)
        self.assertIn(b'Password must be at least 6 characters.', response.data)

    def test_duplicate_email_rejection(self):
        """Test registration reject duplicate email."""
        # Register once
        self.client.post('/register/customer', data={
            'name': 'Name',
            'email': 'dup@example.com',
            'password': 'password123'
        })
        # Register again with same email
        response = self.client.post('/register/customer', data={
            'name': 'Another',
            'email': 'dup@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email already exists.', response.data)

    def test_login_logout_dashboard_redirects(self):
        """Test login workflow and role-based redirect to dashboards."""
        # 1. Register and login customer
        self.client.post('/register/customer', data={
            'name': 'Cust',
            'email': 'cust@example.com',
            'password': 'password123'
        })
        response = self.client.post('/login', data={
            'email': 'cust@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Customer Dashboard', response.data)

        # Try to visit admin dashboard as customer
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Login', response.data)

        # 2. Login admin
        response = self.client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertIn(b'Admin Dashboard', response.data)

        # Logout
        self.client.get('/logout')

        # 3. Provider pending approval login
        self.client.post('/register/provider', data={
            'name': 'Prov',
            'email': 'prov@example.com',
            'password': 'password123',
            'category': 'Design'
        })
        response = self.client.post('/login', data={
            'email': 'prov@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Account Pending Approval', response.data)

    def test_deactivated_user_login(self):
        """Test that deactivated users are blocked from logging in."""
        # Register customer
        self.client.post('/register/customer', data={
            'name': 'Cust',
            'email': 'cust2@example.com',
            'password': 'password123'
        })
        # Deactivate
        with self.app.app_context():
            conn = db.get_db()
            conn.execute("UPDATE users SET is_active = 0 WHERE email = ?", ("cust2@example.com",))
            conn.commit()

        # Login attempts should fail
        response = self.client.post('/login', data={
            'email': 'cust2@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Account deactivated.', response.data)


if __name__ == '__main__':
    unittest.main()
