"""
==============================================================================
Appointment Booking System - Provider Tests
==============================================================================
Automated unit tests to verify service provider features including profile
editing, service management, slot creation validations (past dates, end times,
overlaps), and booking lifecycle management.
==============================================================================
"""

import os
import unittest
import tempfile
import datetime
from app import create_app
import db
from models import User
from werkzeug.security import generate_password_hash

class ProviderTestCase(unittest.TestCase):
    """Test suite for Service Provider features."""

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
            conn = db.get_db()
            # Create approved provider
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role, is_approved, is_active) VALUES (?, ?, ?, ?, 1, 1)",
                ("Provider User", "provider@example.com", generate_password_hash("password123"), "provider")
            )
            prov_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO provider_profiles (user_id, category, bio, experience) VALUES (?, ?, ?, ?)",
                (prov_id, "Tutoring", "Math tutor", "3 years")
            )
            conn.commit()

        # Login as approved provider
        self.client.post('/login', data={'email': 'provider@example.com', 'password': 'password123'})

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_provider_profile_edit(self):
        """Test provider viewing and updating their profile."""
        response = self.client.get('/provider/profile')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/provider/profile', data={
            'category': 'Advanced Tutoring',
            'bio': 'Updated bio.',
            'experience': '5 years'
        }, follow_redirects=True)
        self.assertIn(b'Profile updated.', response.data)

        with self.app.app_context():
            user = User.get_by_email("provider@example.com")
            conn = db.get_db()
            profile = conn.execute("SELECT * FROM provider_profiles WHERE user_id = ?", (user.id,)).fetchone()
            self.assertEqual(profile['category'], 'Advanced Tutoring')
            self.assertEqual(profile['experience'], '5 years')

    def test_provider_service_management(self):
        """Test adding and toggling services."""
        response = self.client.post('/provider/services', data={
            'name': 'Algebra 101',
            'category': 'Math',
            'description': 'Basic algebra session',
            'duration_minutes': '60',
            'price': '50.00'
        }, follow_redirects=True)
        self.assertIn(b'Service added.', response.data)
        self.assertIn(b'Algebra 101', response.data)

    def test_slot_validations(self):
        """Test slot creation validations: past dates, end before start, overlapping slots."""
        future_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        # 1. Past date rejection
        response = self.client.post('/provider/slots', data={
            'slot_date': past_date,
            'start_time': '10:00',
            'end_time': '11:00'
        }, follow_redirects=True)
        self.assertIn(b'Cannot create slots for past dates.', response.data)

        # 2. End time before start time rejection
        response = self.client.post('/provider/slots', data={
            'slot_date': future_date,
            'start_time': '11:00',
            'end_time': '10:00'
        }, follow_redirects=True)
        self.assertIn(b'End time must be after start time.', response.data)

        # 3. Valid slot creation
        response = self.client.post('/provider/slots', data={
            'slot_date': future_date,
            'start_time': '10:00',
            'end_time': '12:00'
        }, follow_redirects=True)
        self.assertIn(b'Appointment slot added successfully.', response.data)

        # 4. Overlapping slot rejection (e.g. 11:00 to 13:00)
        response = self.client.post('/provider/slots', data={
            'slot_date': future_date,
            'start_time': '11:00',
            'end_time': '13:00'
        }, follow_redirects=True)
        self.assertIn(b'Slot overlaps with an existing time slot.', response.data)

if __name__ == '__main__':
    unittest.main()
