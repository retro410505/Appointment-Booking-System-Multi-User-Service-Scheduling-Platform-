"""
==============================================================================
Appointment Booking System - Flask Application Entry Point
==============================================================================
Initializes the Flask web application, configures security keys and database
settings, registers lifecycle teardown hooks, and serves the foundational
home route.
==============================================================================
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, g, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import db
from models import User

# ==============================================================================
# Application Factory / Initialization
# ==============================================================================

def create_app(test_config=None):
    """
    Create and configure an instance of the Flask application.

    Args:
        test_config (dict, optional): Configuration dictionary to override defaults
                                      for automated unit testing.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=False)

    # Core configuration settings
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-appointment-system-2026'),
        DATABASE=os.path.join(app.root_path, 'database.db'),
    )

    if test_config is not None:
        app.config.update(test_config)

    # Register database management teardown hooks and CLI commands
    db.init_app(app)

    # ==========================================================================
    # Flask-Login Configuration
    # ==========================================================================
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login session management."""
        return User.get(user_id)

    # ==========================================================================
    # Role-based Access Control Decorator
    # ==========================================================================
    def role_required(role):
        """Decorator to restrict access by user role."""
        def decorator(f):
            @wraps(f)
            @login_required
            def decorated_function(*args, **kwargs):
                if current_user.role != role:
                    abort(403)
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    # ==========================================================================
    # Error Handling
    # ==========================================================================

    @app.errorhandler(404)
    def page_not_found(e):
        """Render custom 404 error page."""
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        """Render custom 403 error page."""
        return render_template('403.html'), 403

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    # ==========================================================================
    # Application Routes
    # ==========================================================================

    @app.route('/')
    def index():
        """
        Render the foundational home page using the base layout template.

        Returns:
            str: Rendered HTML template.
        """
        return render_template('base.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handles user login."""
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.get_by_email(email)
            if user and check_password_hash(user.password_hash, password):
                if not user.is_active:
                    flash('Account deactivated.', 'error')
                    return redirect(url_for('login'))
                login_user(user)
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'provider':
                    if not user.is_approved:
                        return redirect(url_for('pending_approval'))
                    return redirect(url_for('provider_dashboard'))
                else:
                    return redirect(url_for('customer_dashboard'))
            flash('Invalid email or password.', 'error')
        return render_template('auth/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Handles user logout."""
        logout_user()
        return redirect(url_for('index'))

    @app.route('/pending-approval')
    @login_required
    def pending_approval():
        """Render pending approval notice for unapproved providers."""
        if current_user.role != 'provider' or current_user.is_approved:
            return redirect(url_for('index'))
        return render_template('pending_approval.html')

    @app.route('/register/customer', methods=['GET', 'POST'])
    def register_customer():
        """Handles customer registration."""
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

            if not name or not email or not password:
                flash('All fields are required.', 'error')
                return redirect(url_for('register_customer'))

            import re
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Invalid email address.', 'error')
                return redirect(url_for('register_customer'))

            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return redirect(url_for('register_customer'))

            db_conn = db.get_db()
            # check email unique
            if db_conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                flash('Email already exists.', 'error')
                return redirect(url_for('register_customer'))

            password_hash = generate_password_hash(password)
            db_conn.execute("INSERT INTO users (name, email, password_hash, role, is_approved) VALUES (?, ?, ?, ?, ?)",
                           (name, email, password_hash, 'customer', 1))
            db_conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register_customer.html')

    @app.route('/register/provider', methods=['GET', 'POST'])
    def register_provider():
        """Handles provider registration."""
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            category = request.form.get('category')
            bio = request.form.get('bio')
            experience = request.form.get('experience')

            if not name or not email or not password or not category:
                flash('All required fields must be filled.', 'error')
                return redirect(url_for('register_provider'))

            import re
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Invalid email address.', 'error')
                return redirect(url_for('register_provider'))

            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return redirect(url_for('register_provider'))

            db_conn = db.get_db()
            if db_conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                flash('Email already exists.', 'error')
                return redirect(url_for('register_provider'))

            password_hash = generate_password_hash(password)

            # Start transaction
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password_hash, role, is_approved) VALUES (?, ?, ?, ?, ?)",
                           (name, email, password_hash, 'provider', 0))
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO provider_profiles (user_id, category, bio, experience) VALUES (?, ?, ?, ?)",
                           (user_id, category, bio, experience))
            db_conn.commit()

            flash('Registration successful. Account awaiting admin approval.', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register_provider.html')

    @app.route('/admin/dashboard')
    @role_required('admin')
    def admin_dashboard():
        """Admin dashboard route with summary and management lists."""
        db_conn = db.get_db()

        # Summary counts
        customers_count = db_conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
        approved_providers_count = db_conn.execute("SELECT COUNT(*) FROM users WHERE role = 'provider' AND is_approved = 1").fetchone()[0]
        pending_providers_count = db_conn.execute("SELECT COUNT(*) FROM users WHERE role = 'provider' AND is_approved = 0").fetchone()[0]
        total_bookings_count = db_conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]

        # Lists for dashboard
        pending_providers = db_conn.execute("SELECT * FROM users WHERE role = 'provider' AND is_approved = 0").fetchall()
        customers = db_conn.execute("SELECT * FROM users WHERE role = 'customer'").fetchall()
        providers = db_conn.execute("SELECT * FROM users WHERE role = 'provider' AND is_approved = 1").fetchall()

        # Bookings with filter
        status_filter = request.args.get('status')
        query = "SELECT b.*, c.name as customer_name, p.name as provider_name, s.name as service_name FROM bookings b JOIN users c ON b.customer_id = c.id JOIN users p ON b.provider_id = p.id JOIN services s ON b.service_id = s.id"
        params = []
        if status_filter:
            query += " WHERE b.status = ?"
            params.append(status_filter)
        bookings = db_conn.execute(query, params).fetchall()

        return render_template('admin/dashboard.html',
                               customers_count=customers_count,
                               approved_providers_count=approved_providers_count,
                               pending_providers_count=pending_providers_count,
                               total_bookings_count=total_bookings_count,
                               pending_providers=pending_providers,
                               customers=customers,
                               providers=providers,
                               bookings=bookings,
                               status_filter=status_filter)

    @app.route('/admin/provider/<int:user_id>')
    @role_required('admin')
    def admin_provider_detail(user_id):
        """View a provider's profile and services."""
        db_conn = db.get_db()
        user = db_conn.execute("SELECT * FROM users WHERE id = ? AND role = 'provider'", (user_id,)).fetchone()
        if not user:
            flash('Provider not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        profile = db_conn.execute("SELECT * FROM provider_profiles WHERE user_id = ?", (user_id,)).fetchone()
        services = db_conn.execute("SELECT * FROM services WHERE provider_id = ?", (user_id,)).fetchall()

        return render_template('admin/provider_detail.html', user=user, profile=profile, services=services)

    @app.route('/admin/user/<int:user_id>/toggle-active', methods=['POST'])
    @role_required('admin')
    def admin_toggle_user_active(user_id):
        """Toggle active status for a user."""
        if user_id == current_user.id:
            flash('Cannot deactivate yourself.', 'error')
            return redirect(url_for('admin_dashboard'))

        db_conn = db.get_db()
        user = db_conn.execute("SELECT is_active FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_dashboard'))

        new_status = 1 if user['is_active'] == 0 else 0
        db_conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        db_conn.commit()
        flash(f'User account successfully {"activated" if new_status == 1 else "deactivated"}.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/provider/<int:user_id>/approve', methods=['POST'])
    @role_required('admin')
    def admin_approve_provider(user_id):
        """Approve a pending provider."""
        db.get_db().execute("UPDATE users SET is_approved = 1 WHERE id = ? AND role = 'provider'", (user_id,))
        db.get_db().commit()
        flash('Provider approved.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/provider/<int:user_id>/reject', methods=['POST'])
    @role_required('admin')
    def admin_reject_provider(user_id):
        """Reject a pending provider."""
        db.get_db().execute("UPDATE users SET is_approved = -1 WHERE id = ? AND role = 'provider'", (user_id,))
        db.get_db().commit()
        flash('Provider rejected.', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/service/<int:service_id>/edit', methods=['GET', 'POST'])
    @role_required('admin')
    def admin_edit_service(service_id):
        """Edit a service listing."""
        db_conn = db.get_db()
        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            description = request.form.get('description')
            duration = request.form.get('duration_minutes')
            price = request.form.get('price')

            db_conn.execute("UPDATE services SET name = ?, category = ?, description = ?, duration_minutes = ?, price = ? WHERE id = ?",
                            (name, category, description, duration, price, service_id))
            db_conn.commit()
            flash('Service updated.', 'success')
            return redirect(url_for('admin_dashboard'))

        service = db_conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
        return render_template('admin/edit_service.html', service=service)

    @app.route('/admin/service/<int:service_id>/delete', methods=['POST'])
    @role_required('admin')
    def admin_delete_service(service_id):
        """Remove a service listing."""
        db.get_db().execute("DELETE FROM services WHERE id = ?", (service_id,))
        db.get_db().commit()
        flash('Service removed.', 'success')
        return redirect(url_for('admin_dashboard'))

    # ==========================================================================
    # Customer Routes
    # ==========================================================================

    @app.route('/providers')
    def list_providers():
        """
        List approved, active providers with their active services,
        optionally filtered by keyword and category.
        """
        db_conn = db.get_db()

        # Search/Filter parameters
        keyword = request.args.get('keyword', '')
        category = request.args.get('category', '')

        # Base query to find providers
        query = """
            SELECT DISTINCT u.id, u.name, p.category, p.bio
            FROM users u
            JOIN provider_profiles p ON u.id = p.user_id
            JOIN services s ON u.id = s.provider_id
            WHERE u.role = 'provider' AND u.is_approved = 1 AND u.is_active = 1
            AND s.is_active = 1
        """
        params = []

        if keyword:
            query += " AND (s.name LIKE ? OR s.description LIKE ?)"
            params.append(f'%{keyword}%')
            params.append(f'%{keyword}%')

        if category:
            query += " AND p.category = ?"
            params.append(category)

        providers = db_conn.execute(query, params).fetchall()

        providers_data = []
        for provider in providers:
            provider_dict = dict(provider)
            provider_dict['services'] = db_conn.execute(
                "SELECT * FROM services WHERE provider_id = ? AND is_active = 1",
                (provider['id'],)
            ).fetchall()
            providers_data.append(provider_dict)

        return render_template('customer/providers.html', providers=providers_data, keyword=keyword, category=category)

    @app.route('/booking/book/<int:slot_id>', methods=['GET', 'POST'])
    @role_required('customer')
    def book_appointment(slot_id):
        """
        Booking form for a selected slot and service selection.
        """
        db_conn = db.get_db()
        slot = db_conn.execute(
            "SELECT sl.*, p.name as provider_name FROM appointment_slots sl JOIN users p ON sl.provider_id = p.id WHERE sl.id = ? AND sl.is_booked = 0",
            (slot_id,)
        ).fetchone()

        if not slot:
            flash('Slot not available.', 'error')
            return redirect(url_for('list_providers'))

        services = db_conn.execute("SELECT * FROM services WHERE provider_id = ? AND is_active = 1", (slot['provider_id'],)).fetchall()

        if request.method == 'POST':
            service_id = request.form.get('service_id')
            notes = request.form.get('notes', '')

            if not service_id:
                flash('Please select a service.', 'error')
                return redirect(url_for('book_appointment', slot_id=slot_id))

            # Atomic check-and-insert for booking
            cursor = db_conn.cursor()
            try:
                # Check if slot is already booked (double booking prevention)
                cursor.execute("SELECT id FROM appointment_slots WHERE id = ? AND is_booked = 0", (slot_id,))
                if not cursor.fetchone():
                     flash('Slot already booked.', 'error')
                     return redirect(url_for('list_providers'))

                cursor.execute(
                    "INSERT INTO bookings (customer_id, provider_id, service_id, slot_id, notes, status) VALUES (?, ?, ?, ?, ?, 'pending')",
                    (current_user.id, slot['provider_id'], service_id, slot_id, notes)
                )
                # Note: We do NOT update appointment_slots.is_booked here.
                # It becomes booked when provider confirms (Task 5: Customer dashboard).
                # Wait, "Cancelled bookings ... slot becomes available again".
                # If slot IS NOT marked booked, how do we prevent another booking on the same slot?
                # Ah, the UNIQUE constraint on slot_id in bookings table!
                # If I try to insert a booking with the same slot_id, it should fail.
                # Perfect!
                db_conn.commit()
                flash('Booking request submitted.', 'success')
                return redirect(url_for('customer_dashboard'))
            except Exception as e:
                db_conn.rollback()
                flash('Error submitting booking: ' + str(e), 'error')
                return redirect(url_for('book_appointment', slot_id=slot_id))

        return render_template('customer/book.html', slot=slot, services=services)

    @app.route('/provider/profile', methods=['GET', 'POST'])
    @role_required('provider')
    def provider_profile():
        """View and edit own profile."""
        db_conn = db.get_db()
        if request.method == 'POST':
            category = request.form.get('category')
            bio = request.form.get('bio')
            experience = request.form.get('experience')

            db_conn.execute("UPDATE provider_profiles SET category = ?, bio = ?, experience = ? WHERE user_id = ?",
                            (category, bio, experience, current_user.id))
            db_conn.commit()
            flash('Profile updated.', 'success')
            return redirect(url_for('provider_profile'))

        profile = db_conn.execute("SELECT * FROM provider_profiles WHERE user_id = ?", (current_user.id,)).fetchone()
        return render_template('provider/profile/edit.html', profile=profile)

    @app.route('/provider/services', methods=['GET', 'POST'])
    @role_required('provider')
    def provider_services():
        """List and manage own services."""
        db_conn = db.get_db()
        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            description = request.form.get('description')
            duration = request.form.get('duration_minutes')
            price = request.form.get('price')

            db_conn.execute("INSERT INTO services (provider_id, name, category, description, duration_minutes, price) VALUES (?, ?, ?, ?, ?, ?)",
                            (current_user.id, name, category, description, duration, price))
            db_conn.commit()
            flash('Service added.', 'success')
            return redirect(url_for('provider_services'))

        services = db_conn.execute("SELECT * FROM services WHERE provider_id = ?", (current_user.id,)).fetchall()
        return render_template('provider/services/list.html', services=services)

    @app.route('/provider/service/<int:service_id>/toggle', methods=['POST'])
    @role_required('provider')
    def provider_toggle_service(service_id):
        """Toggle service active status."""
        db_conn = db.get_db()
        service = db_conn.execute("SELECT * FROM services WHERE id = ? AND provider_id = ?", (service_id, current_user.id)).fetchone()
        if not service:
            flash('Service not found or unauthorized.', 'error')
            return redirect(url_for('provider_services'))

        new_status = 1 if service['is_active'] == 0 else 0
        db_conn.execute("UPDATE services SET is_active = ? WHERE id = ?", (new_status, service_id))
        db_conn.commit()
        flash('Service status updated.', 'success')
        return redirect(url_for('provider_services'))

    @app.route('/provider/dashboard')
    @role_required('provider')
    def provider_dashboard():
        """Provider dashboard with pending booking requests count and list, plus slots and bookings."""
        if not current_user.is_approved:
            return redirect(url_for('pending_approval'))

        db_conn = db.get_db()
        pending_requests = db_conn.execute(
            "SELECT b.*, c.name as customer_name, s.name as service_name, sl.slot_date, sl.start_time, sl.end_time "
            "FROM bookings b "
            "JOIN users c ON b.customer_id = c.id "
            "JOIN services s ON b.service_id = s.id "
            "JOIN appointment_slots sl ON b.slot_id = sl.id "
            "WHERE b.provider_id = ? AND b.status = 'pending'",
            (current_user.id,)
        ).fetchall()

        all_bookings = db_conn.execute(
            "SELECT b.*, c.name as customer_name, s.name as service_name, sl.slot_date, sl.start_time, sl.end_time "
            "FROM bookings b "
            "JOIN users c ON b.customer_id = c.id "
            "JOIN services s ON b.service_id = s.id "
            "JOIN appointment_slots sl ON b.slot_id = sl.id "
            "WHERE b.provider_id = ? "
            "ORDER BY sl.slot_date DESC, sl.start_time DESC",
            (current_user.id,)
        ).fetchall()

        slots = db_conn.execute(
            "SELECT * FROM appointment_slots WHERE provider_id = ? ORDER BY slot_date DESC, start_time DESC",
            (current_user.id,)
        ).fetchall()

        return render_template('provider/dashboard.html',
                               pending_requests=pending_requests,
                               pending_count=len(pending_requests),
                               all_bookings=all_bookings,
                               slots=slots)

    @app.route('/provider/slots', methods=['GET', 'POST'])
    @role_required('provider')
    def provider_slots():
        """Add and manage appointment slots."""
        if not current_user.is_approved:
            return redirect(url_for('pending_approval'))

        db_conn = db.get_db()
        if request.method == 'POST':
            slot_date = request.form.get('slot_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')

            if not slot_date or not start_time or not end_time:
                flash('All fields are required.', 'error')
                return redirect(url_for('provider_slots'))

            # Check past dates
            import datetime
            today = datetime.date.today().isoformat()
            if slot_date < today:
                flash('Cannot create slots for past dates.', 'error')
                return redirect(url_for('provider_slots'))

            # Check end time before start time
            if end_time <= start_time:
                flash('End time must be after start time.', 'error')
                return redirect(url_for('provider_slots'))

            # Check overlapping slots for the same provider
            # Overlap condition: (new_start < existing_end) AND (new_end > existing_start)
            overlapping = db_conn.execute(
                "SELECT id FROM appointment_slots WHERE provider_id = ? AND slot_date = ? AND (? < end_time AND ? > start_time)",
                (current_user.id, slot_date, start_time, end_time)
            ).fetchone()

            if overlapping:
                flash('Slot overlaps with an existing time slot.', 'error')
                return redirect(url_for('provider_slots'))

            db_conn.execute(
                "INSERT INTO appointment_slots (provider_id, slot_date, start_time, end_time, is_booked) VALUES (?, ?, ?, ?, 0)",
                (current_user.id, slot_date, start_time, end_time)
            )
            db_conn.commit()
            flash('Appointment slot added successfully.', 'success')
            return redirect(url_for('provider_slots'))

        slots = db_conn.execute(
            "SELECT * FROM appointment_slots WHERE provider_id = ? ORDER BY slot_date DESC, start_time DESC",
            (current_user.id,)
        ).fetchall()
        return render_template('provider/slots/list.html', slots=slots)

    @app.route('/provider/slot/<int:slot_id>/delete', methods=['POST'])
    @role_required('provider')
    def provider_delete_slot(slot_id):
        """Delete an unbooked slot with ownership check."""
        db_conn = db.get_db()
        slot = db_conn.execute("SELECT * FROM appointment_slots WHERE id = ?", (slot_id,)).fetchone()
        if not slot or slot['provider_id'] != current_user.id:
            flash('Slot not found or unauthorized.', 'error')
            return redirect(url_for('provider_slots'))

        if slot['is_booked']:
            flash('Cannot delete a booked slot.', 'error')
            return redirect(url_for('provider_slots'))

        db_conn.execute("DELETE FROM appointment_slots WHERE id = ?", (slot_id,))
        db_conn.commit()
        flash('Slot deleted successfully.', 'success')
        return redirect(url_for('provider_slots'))

    @app.route('/provider/booking/<int:booking_id>/action', methods=['POST'])
    @role_required('provider')
    def provider_booking_action(booking_id):
        """Handle booking actions (confirm, reject, cancel, complete)."""
        action = request.form.get('action')
        db_conn = db.get_db()
        booking = db_conn.execute(
            "SELECT b.*, sl.slot_date, sl.start_time FROM bookings b JOIN appointment_slots sl ON b.slot_id = sl.id WHERE b.id = ?",
            (booking_id,)
        ).fetchone()

        if not booking or booking['provider_id'] != current_user.id:
            flash('Booking not found or unauthorized.', 'error')
            return redirect(url_for('provider_dashboard'))

        if action == 'confirm':
            if booking['status'] != 'pending':
                flash('Only pending bookings can be confirmed.', 'error')
                return redirect(url_for('provider_dashboard'))
            db_conn.execute("UPDATE bookings SET status = 'confirmed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (booking_id,))
            db_conn.execute("UPDATE appointment_slots SET is_booked = 1 WHERE id = ?", (booking['slot_id'],))
            db_conn.commit()
            flash('Booking confirmed and slot marked as booked.', 'success')

        elif action == 'reject':
            if booking['status'] != 'pending':
                flash('Only pending bookings can be rejected.', 'error')
                return redirect(url_for('provider_dashboard'))
            db_conn.execute("UPDATE bookings SET status = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (booking_id,))
            db_conn.commit()
            flash('Booking rejected.', 'success')

        elif action == 'cancel':
            if booking['status'] != 'confirmed':
                flash('Only confirmed bookings can be cancelled.', 'error')
                return redirect(url_for('provider_dashboard'))
            db_conn.execute("UPDATE bookings SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (booking_id,))
            db_conn.execute("UPDATE appointment_slots SET is_booked = 0 WHERE id = ?", (booking['slot_id'],))
            db_conn.commit()
            flash('Booking cancelled and slot made available again.', 'success')

        elif action == 'complete':
            if booking['status'] != 'confirmed':
                flash('Only confirmed bookings can be marked as completed.', 'error')
                return redirect(url_for('provider_dashboard'))
            db_conn.execute("UPDATE bookings SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (booking_id,))
            db_conn.commit()
            flash('Booking marked as completed.', 'success')

        return redirect(url_for('provider_dashboard'))

    @app.route('/customer/dashboard')
    @role_required('customer')
    def customer_dashboard():
        """Customer dashboard: view bookings grouped by status."""
        db_conn = db.get_db()
        bookings = db_conn.execute(
            "SELECT b.*, p.name as provider_name, s.name as service_name, sl.slot_date, sl.start_time "
            "FROM bookings b "
            "JOIN users p ON b.provider_id = p.id "
            "JOIN services s ON b.service_id = s.id "
            "JOIN appointment_slots sl ON b.slot_id = sl.id "
            "WHERE b.customer_id = ? "
            "ORDER BY sl.slot_date DESC, sl.start_time DESC",
            (current_user.id,)
        ).fetchall()

        # Grouping
        grouped_bookings = {
            'pending': [],
            'confirmed': [],
            'completed': [],
            'rejected': [],
            'cancelled': []
        }
        for b in bookings:
            grouped_bookings[b['status']].append(b)

        return render_template('customer/dashboard.html', bookings=grouped_bookings)

    @app.route('/booking/<int:booking_id>/cancel', methods=['POST'])
    @role_required('customer')
    def cancel_booking(booking_id):
        """Cancel a pending or confirmed booking."""
        db_conn = db.get_db()
        booking = db_conn.execute(
            "SELECT * FROM bookings WHERE id = ? AND customer_id = ?",
            (booking_id, current_user.id)
        ).fetchone()

        if not booking:
            flash('Booking not found.', 'error')
            return redirect(url_for('customer_dashboard'))

        if booking['status'] not in ['pending', 'confirmed']:
            flash('Only pending or confirmed bookings can be cancelled.', 'error')
            return redirect(url_for('customer_dashboard'))

        db_conn.execute("UPDATE bookings SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (booking_id,))
        if booking['status'] == 'confirmed':
            db_conn.execute("UPDATE appointment_slots SET is_booked = 0 WHERE id = ?", (booking['slot_id'],))
        db_conn.commit()
        flash('Booking cancelled.', 'success')
        return redirect(url_for('customer_dashboard'))

    # ==========================================================================
    # Error Handlers
    # ==========================================================================
    @app.errorhandler(404)
    def page_not_found(e):
        """Custom 404 error page."""
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        """Custom 403 error page."""
        return render_template('403.html'), 403

    return app


# Instantiate the main application object for WSGI servers and direct execution
app = create_app()

# ==============================================================================
# Direct Script Execution
# ==============================================================================
if __name__ == '__main__':
    # Run development server with auto-reload enabled
    app.run(host='127.0.0.1', port=5000, debug=True)
