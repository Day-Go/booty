"""
Data models for the mock project
"""

from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class User:
    """User model representing application users"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


@dataclass
class Post:
    """Post model representing user content"""
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary representation"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': self.tags or []
        }