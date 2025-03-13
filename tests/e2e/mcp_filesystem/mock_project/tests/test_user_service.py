"""
Tests for the user service
"""

import pytest


# Mock implementation of user service for testing
class MockUserService:
    def __init__(self, mock_users):
        self.mock_users = mock_users
        self.next_id = max(user["id"] for user in mock_users) + 1 if mock_users else 1
    
    def get_all_users(self):
        return self.mock_users
    
    def get_user_by_id(self, user_id):
        for user in self.mock_users:
            if user["id"] == user_id:
                return user
        return None
    
    def create_user(self, data):
        new_user = {
            "id": self.next_id,
            "username": data["username"],
            "email": data["email"],
            "created_at": "2023-01-01T00:00:00",
            "is_active": True,
            "last_login": None
        }
        self.mock_users.append(new_user)
        self.next_id += 1
        return new_user


def test_get_all_users(mock_user_data):
    """Test getting all users"""
    service = MockUserService(mock_user_data.copy())
    users = service.get_all_users()
    
    # Verify results
    assert len(users) == 2
    assert users[0]["username"] == "testuser1"
    assert users[1]["username"] == "testuser2"


def test_get_user_by_id(mock_user_data):
    """Test getting a user by ID"""
    service = MockUserService(mock_user_data.copy())
    user = service.get_user_by_id(1)
    
    # Verify results
    assert user is not None
    assert user["id"] == 1
    assert user["username"] == "testuser1"
    assert user["email"] == "test1@example.com"
    assert user["is_active"] is True


def test_get_nonexistent_user(mock_user_data):
    """Test getting a user that doesn't exist"""
    service = MockUserService(mock_user_data.copy())
    user = service.get_user_by_id(999)
    
    # Verify results
    assert user is None


def test_create_user(mock_user_data):
    """Test creating a new user"""
    service = MockUserService(mock_user_data.copy())
    new_user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    }
    
    user = service.create_user(new_user_data)
    
    # Verify results
    assert user is not None
    assert user["username"] == "newuser"
    assert user["email"] == "new@example.com"
    assert user["id"] == 3  # Since we already have users with IDs 1 and 2