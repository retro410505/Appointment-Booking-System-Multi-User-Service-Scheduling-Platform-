# Appointment Booking System

## Project Description
The Appointment Booking System is a full-stack web application built using **Python (Flask)** and **SQLite**. It provides an end-to-end appointment scheduling platform connecting customers with professional service providers (e.g., tutors, consultants, technicians), complete with a robust administrative dashboard for user and booking oversight.

### Key Features
- **Role-Based Access Control (RBAC)**: Separate interfaces and permissions for `Admin`, `Service Provider`, and `Customer`.
- **Approval Workflow**: Service providers must be approved by an administrator before they can publish services or schedule appointment slots.
- **Dynamic Slot Management**: Providers can set availability windows with overlap protection.
- **Booking Lifecycle**: Tracks bookings from `pending` -> `confirmed` / `rejected` -> `completed` or `cancelled`, with automatic slot release on cancellation.
- **Security**: Password hashing via Werkzeug, CSRF/SQL injection protection using parameterized SQLite queries, and custom error pages (403, 404).

---

## Setup Steps

1. **Clone or Extract the Project Directory**:
   Open a terminal in the project root directory.

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the Database**:
   The application automatically handles database schema setup on first run via `db.py`, or you can manually initialize it using:
   ```bash
   python -m flask --app app init-db
   ```

4. **Seed the Administrator Account**:
   Run the seed script to create the default administrative account:
   ```bash
   python seed_admin.py
   ```

---

## How to Run the Development Server

Start the Flask development server:
```bash
python app.py
```
Open your web browser and navigate to:
`http://127.0.0.1:5000`

---

## Default Login Credentials

- **Admin Account**:
  - Email: `admin@example.com`
  - Password: `admin123`

---

## Full Test Walkthrough

Follow this step-by-step walkthrough to verify the complete end-to-end functionality of the system:

1. **Provider Registration & Admin Approval**:
   - Navigate to `http://127.0.0.1:5000/register/provider`.
   - Register a new service provider (e.g., Name: *John Tutor*, Email: *john@tutor.com*, Password: *password123*, Category: *Education*).
   - Log out, then log in as the Admin (`admin@example.com` / `admin123`).
   - On the Admin Dashboard, locate John Tutor under **Pending Providers** and click **Approve**.

2. **Provider Setup (Services & Slots)**:
   - Log out and log in as the approved provider (`john@tutor.com` / `password123`).
   - Go to **Services** and add a new service (e.g., Name: *Math Tutoring*, Category: *Education*, Duration: *60* minutes, Price: *50.0*).
   - Go to **Slots** and add an availability slot for a future date (e.g., Date: *2026-11-15*, Start Time: *10:00*, End Time: *11:00*).

3. **Customer Registration & Booking**:
   - Register a new customer account via `http://127.0.0.1:5000/register/customer` (e.g., Name: *Alice Student*, Email: *alice@student.com*, Password: *password123*).
   - Log in as the customer and navigate to **Providers / Services**.
   - Find *John Tutor* and click **Book Slot** for the Math Tutoring slot created earlier. Add any optional notes and submit the request.

4. **Provider Confirmation**:
   - Log out and log in as the provider (`john@tutor.com`).
   - On the Provider Dashboard, view the **Pending Booking Request** from Alice Student.
   - Click **Confirm**. The slot is now officially reserved and marked as booked.

5. **Provider Completion**:
   - After the appointment time passes (or directly in the dashboard), locate the confirmed booking under **All Bookings**.
   - Click **Complete** to transition the booking status to `completed`.

6. **Customer Verification**:
   - Log in as the customer (`alice@student.com`) and check your **Customer Dashboard**.
   - Confirm that the booking status is correctly displayed as `completed`.
