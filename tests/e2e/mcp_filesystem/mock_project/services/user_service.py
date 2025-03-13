"""
User service for handling user-related operations
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from database.connection import get_db_session
from database.models import User


class UserService:
    """Service class for user-related operations"""
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from the database
        
        Returns:
            List[Dict[str, Any]]: List of user dictionaries
        """
        session = get_db_session()
        users = session.query(User).all()
        
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
            
        session.close()
        return result
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID
        
        Args:
            user_id (int): The user ID to find
            
        Returns:
            Optional[Dict[str, Any]]: The user dictionary or None if not found
        """
        session = get_db_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            session.close()
            return None
        
        result = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
        
        session.close()
        return result
    
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            data (Dict[str, Any]): User data including username, email, password
            
        Returns:
            Dict[str, Any]: The created user dictionary
        """
        session = get_db_session()
        
        # Create password hash (in a real app, we would use a proper password hashing function)
        password_hash = f"hashed_{data['password']}"
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        session.add(new_user)
        session.commit()
        
        # Prepare response
        result = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'created_at': new_user.created_at.isoformat(),
            'is_active': new_user.is_active,
            'last_login': None
        }
        
        session.close()
        return result