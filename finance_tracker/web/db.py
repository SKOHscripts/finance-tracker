"""
Database module for managing SQLAlchemy sessions in the finance tracker application.

This module provides a cached database session factory using SQLAlchemy and SQLModel.
It reads the database connection URL from the application configuration and creates
engine and session objects for database operations. The session is cached using
Streamlit's caching mechanism to optimize performance and resource usage.

The module is specifically designed for use with Streamlit applications and should
be imported wherever database access is required.
"""
import uuid

import streamlit as st
from sqlmodel import create_engine, Session

from finance_tracker.config import DATABASE_URL


def get_db_path():
    """Generate and return session-specific database file path.

    Creates a unique session ID if not already present in streamlit
    session state and returns path to temporary SQLite database file.
    """
    # Generate unique session ID to isolate data between different users/sessions

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    # Use temp directory with session-specific filename to ensure cleanup and isolation

    return f"/tmp/finance_{st.session_state.session_id}.db"


def get_engine():
    """Create and return SQLAlchemy engine for session database.

    Retrieves the session-specific database path and creates a SQLite
    engine using SQLAlchemy's create_engine function.
    """
    db_path = get_db_path()
    # Build SQLite URL from dynamic path (enables per-session database)
    sqlite_url = f"sqlite:///{db_path}"

    return create_engine(sqlite_url)


def get_session():
    """Create and return SQLAlchemy Session for database operations.

    Obtains an engine from get_engine and returns a new Session object
    for executing database queries.
    """
    engine = get_engine()
    # Return raw Session for caller to manage lifecycle (open/close)

    return Session(engine)
