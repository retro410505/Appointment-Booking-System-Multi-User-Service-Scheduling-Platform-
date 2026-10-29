"""
==============================================================================
Appointment Booking System - Database Management Helper
==============================================================================
This module provides connection management, row serialization helpers,
and database initialization routines for SQLite. It supports both active
Flask application contexts and standalone administrative execution (e.g., seeding).
==============================================================================
"""

import os
import sqlite3
from flask import current_app, g, has_app_context

# Default path to SQLite database file in the project directory
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')


def get_db_path():
    """
    Determine the active SQLite database path.

    Returns:
        str: Absolute or configured path to the SQLite database file.
    """
    if has_app_context() and 'DATABASE' in current_app.config:
        return current_app.config['DATABASE']
    return DEFAULT_DB_PATH


def get_db():
    """
    Obtain an open SQLite database connection.

    If executed within a Flask application context, the connection is cached
    on Flask's application context global `g` for the duration of the request.
    Configures row_factory to sqlite3.Row so columns are accessible by name,
    and explicitly enables foreign key constraint enforcement.

    Returns:
        sqlite3.Connection: Configured SQLite database connection.
    """
    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(
                get_db_path(),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable dictionary-like access to database columns (row['column_name'])
            g.db.row_factory = sqlite3.Row
            # Enforce foreign key constraints in SQLite
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    # Standalone connection when called outside Flask request context (e.g., seed scripts)
    conn = sqlite3.connect(
        get_db_path(),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_db(e=None):
    """
    Close the database connection associated with the current application context.

    This function is registered with Flask's teardown_appcontext hook to ensure
    connections are closed reliably after each request.

    Args:
        e (Exception, optional): Unhandled exception that triggered teardown, if any.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(db_path=None):
    """
    Initialize the database using the SQL statements defined in schema.sql.

    Reads the schema definition file and executes all DDL statements to create
    required tables, constraints, and relationships.

    Args:
        db_path (str, optional): Target database path override. Defaults to active DB.
    """
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, mode='r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Execute all table creation DDL commands from schema.sql
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def init_app(app):
    """
    Register database lifecycle hooks and CLI commands with the Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    # Register teardown handler to close connection at request end
    app.teardown_appcontext(close_db)

    # Register CLI command `flask init-db`
    import click

    @app.cli.command('init-db')
    def init_db_command():
        """Initialize and create all database tables from schema.sql."""
        init_db()
        click.echo('Database initialized successfully from schema.sql.')
