"""
Pytest configuration for mock project tests
"""

import os
import pytest
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Note: In a real project, these would be imported:
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from database.connection import Base
# from database.models import User, Post, Tag


@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    return [
        {
            "id": 1,
            "username": "testuser1",
            "email": "test1@example.com",
            "created_at": "2023-01-01T00:00:00",
            "is_active": True,
            "last_login": None
        },
        {
            "id": 2,
            "username": "testuser2",
            "email": "test2@example.com",
            "created_at": "2023-01-02T00:00:00",
            "is_active": False,
            "last_login": None
        }
    ]


@pytest.fixture
def mock_post_data():
    """Mock post data for testing"""
    return [
        {
            "id": 1,
            "title": "Test Post 1",
            "content": "This is test content for the first post",
            "author_id": 1,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": None,
            "tags": ["test", "example"]
        }
    ]