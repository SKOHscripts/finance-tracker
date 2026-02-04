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

from finance_tracker.config import DATABASE_URL


@st.cache_resource
def get_session() -> Session:
    """
    Crée et retourne une session de base de données.

    Cette fonction utilise une URL de base de données définie dans la configuration
    pour initialiser une session SQLAlchemy. La session est mise en cache pour
    éviter les reconstructions inutiles.

    Returns
    -------
    Session
        Une instance de session SQLAlchemy connectée à la base de données.
    """
    # Create a database engine using the URL from config
    engine = create_engine(DATABASE_URL, echo=False)

    # Return a new session bound to the engine

    return Session(engine)
