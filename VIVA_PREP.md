### Viva Q&A: 10 Questions Your Teacher Might Ask

1. **How do you prevent SQL injection?**
   - Answer: By using parameterized queries (`?` placeholders) in all database interactions, which ensures user input is treated as data, not executable code.

2. **What is the purpose of the `@login_required` decorator?**
   - Answer: It ensures that only authenticated users can access specific routes, redirecting unauthenticated users to the login page.

3. **How does the system ensure role-based access control?**
   - Answer: Using a custom `role_required` decorator that checks the `current_user.role` against the required role before allowing access to a route.

4. **Why is `PRAGMA foreign_keys = ON;` necessary?**
   - Answer: By default, SQLite doesn't enforce foreign key constraints. Enabling this ensures data integrity, such as preventing the deletion of a user if they have active bookings.

5. **How does the booking system handle concurrent bookings on the same slot?**
   - Answer: The `bookings` table has a `UNIQUE` constraint on `slot_id`. If two users attempt to book the same slot simultaneously, the first transaction commits, and the second one will fail due to a database constraint violation.

6. **What is the difference between `authentication` and `authorization` in this app?**
   - Answer: Authentication verifies who the user is (login), while authorization determines what the authenticated user is allowed to do (roles like admin/provider/customer).

7. **How are passwords stored securely?**
   - Answer: We use `generate_password_hash` to store a salted hash of the password, and `check_password_hash` to verify passwords during login, never storing plaintext passwords.

8. **How does the application manage database sessions?**
   - Answer: Using a teardown hook (`@app.teardown_appcontext`) to close the database connection after each request, ensuring resources are freed.

9. **Why is the `provider_profiles` table separated from the `users` table?**
   - Answer: It follows database normalization principles, keeping common user data in `users` and specific professional details only for providers, maintaining a clean 1:1 relationship.

10. **How would you deploy this to production?**
    - Answer: Replace the Flask development server with a production-ready WSGI server like `gunicorn`, use a real database (PostgreSQL/MySQL), set `DEBUG=False`, and use strong, environment-variable-loaded `SECRET_KEY`.
