"""
Database module for managing SQLAlchemy sessions in the finance tracker application.

This module provides a cached database session factory using SQLAlchemy and SQLModel.
It reads the database connection URL from the application configuration and creates
engine and session objects for database operations. The session is cached using
Streamlit's caching mechanism to optimize performance and resource usage.

The module is specifically designed for use with Streamlit applications and should
be imported wherever database access is required.
"""

import streamlit as st
from sqlmodel import Session, create_engine
import uuid
import streamlit as st
from sqlmodel import create_engine, Session

from finance_tracker.config import DATABASE_URL


def get_db_path():
    # Création d'un identifiant de session unique si inexistant

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    # Fichier temporaire isolé pour la session en cours

    return f"/tmp/finance_{st.session_state.session_id}.db"


def get_engine():
    db_path = get_db_path()
    # Utilisation du chemin dynamique
    sqlite_url = f"sqlite:///{db_path}"

    return create_engine(sqlite_url)


def get_session():
    engine = get_engine()
    # Retourner l'objet directement (sans 'with' et 'yield')

    return Session(engine)
