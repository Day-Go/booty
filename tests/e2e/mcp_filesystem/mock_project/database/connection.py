"""
Database connection module
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

# Base class for all database models
Base = declarative_base()

def get_db_connection() -> Engine:
    """
    Create and return a database connection engine
    
    Returns:
        sqlalchemy.engine.Engine: Database connection engine
    """
    # Get database URL from environment or use default SQLite
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///mock_project.db')
    
    # Create engine with appropriate settings
    engine = create_engine(
        db_url,
        echo=False,  # Set to True for debug SQL output
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    return engine

def get_db_session():
    """
    Create and return a database session
    
    Returns:
        sqlalchemy.orm.Session: Database session
    """
    engine = get_db_connection()
    Session = sessionmaker(bind=engine)
    return Session()