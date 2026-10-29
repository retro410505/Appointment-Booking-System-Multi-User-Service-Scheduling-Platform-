"""
==============================================================================
Appointment Booking System - User Model
==============================================================================
Defines the User class and Flask-Login integration, mapping the database
'users' table to the application's user object.
==============================================================================
"""

from flask_login import UserMixin
from db import get_db

class User(UserMixin):
    """
    Represents an application user authenticated via Flask-Login.

    Attributes:
        id (int): Unique user identifier.
        name (str): User's display name.
        email (str): User's unique email address.
        password_hash (str): Werkzeug-hashed password.
        role (str): 'admin', 'provider', or 'customer'.
        is_approved (bool): Approval status for providers.
        is_active (bool): Account active status.
    """

    def __init__(self, user_data):
        self.id = user_data['id']
        self.name = user_data['name']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.role = user_data['role']
        self.is_approved = bool(user_data['is_approved'])
        self.is_active = bool(user_data['is_active'])

    @staticmethod
    def get(user_id):
        """
        Fetch a user instance by ID from the database.

        Args:
            user_id (int): The unique ID of the user.

        Returns:
            User: The User object if found, else None.
        """
        db = get_db()
        user_data = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def get_by_email(email):
        """
        Fetch a user instance by email from the database.

        Args:
            email (str): The email address of the user.

        Returns:
            User: The User object if found, else None.
        """
        db = get_db()
        user_data = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user_data:
            return User(user_data)
        return None

    def get_id(self):
        """
        Return the user's ID as a string, required by Flask-Login.
        """
        return str(self.id)

    @property
    def is_active(self):
        """
        Return whether the account is active. Required by Flask-Login.
        """
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value
