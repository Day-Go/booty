"""
Test helpers for MCP filesystem testing.

These utilities help maintain test-source coupling by:
1. Automatically generating mock implementations from real implementations
2. Validating command formats
3. Providing shared fixtures and utilities
"""

import inspect
import re
import sys
import os
import json
from typing import Dict, Any, List, Callable, Optional, Type, Union
from unittest.mock import MagicMock, patch

# Add project root to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.mcp_filesystem_client import MCPFilesystemClient
from src.mcp_command_handler import MCPCommandHandler

class MockResponse:
    """Mock response for requests."""
    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)
    
    def json(self) -> Dict[str, Any]:
        return self.json_data
    
    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


def create_synchronized_method(original_method: Callable, mock_implementation: Optional[Callable] = None) -> Callable:
    """
    Create a synchronized mock method that matches the signature of the original method.
    
    Args:
        original_method: The original method to mock
        mock_implementation: Optional custom implementation for the mock
        
    Returns:
        A function that has the same signature as the original method
    """
    if mock_implementation:
        return mock_implementation
    
    # Get signature of original method
    sig = inspect.signature(original_method)
    
    # Create default mock implementation
    def default_mock_implementation(*args, **kwargs):
        # Just return a MagicMock that would return whatever is needed
        return MagicMock()
    
    # Return the default implementation with the original signature
    default_mock_implementation.__signature__ = sig
    default_mock_implementation.__name__ = original_method.__name__
    default_mock_implementation.__doc__ = f"Mock of {original_method.__name__} with signature {sig}"
    
    return default_mock_implementation


def generate_synchronized_mock(original_class: Type, 
                              essential_methods: List[str] = None,
                              method_implementations: Dict[str, Callable] = None) -> Type:
    """
    Generate a mock class that stays synchronized with the original class's interface.
    
    Args:
        original_class: The original class to mock
        essential_methods: List of method names that must be implemented
        method_implementations: Custom implementations for specific methods
        
    Returns:
        A mock class type that has the same interface as the original
    """
    essential_methods = essential_methods or []
    method_implementations = method_implementations or {}
    
    # Get all public methods from the original class
    public_methods = {name: method for name, method in inspect.getmembers(original_class) 
                     if not name.startswith('_') and callable(method)}
    
    # Create attributes dictionary for the new class
    mock_attrs = {}
    
    # Add __init__ method
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        # Set additional attributes if needed
        for name, value in kwargs.items():
            setattr(self, name, value)
    
    mock_attrs['__init__'] = __init__
    
    # Add synchronized mock methods
    for name, method in public_methods.items():
        # Check if we need this method
        if name in essential_methods or not essential_methods:
            # Use custom implementation if provided
            if name in method_implementations:
                mock_attrs[name] = method_implementations[name]
            else:
                # Create synchronized mock method
                mock_attrs[name] = create_synchronized_method(method)
    
    # Create and return the new mock class
    return type(f"Mock{original_class.__name__}", (), mock_attrs)


def extract_command_format(command_xml: str) -> Dict[str, Any]:
    """
    Extract command format from XML command string.
    This is useful for validating command formats in tests.
    
    Args:
        command_xml: XML command string
        
    Returns:
        Dictionary with command details
    """
    command_info = {}
    
    # Extract command type
    command_match = re.search(r'<(\w+)[ >]', command_xml)
    if command_match:
        command_type = command_match.group(1)
        command_info["type"] = command_type
        
        # Extract action based on command type
        if command_type == "read":
            command_info["action"] = "read"
            path_match = re.search(r'path="([^"]*)"', command_xml)
            if path_match:
                command_info["path"] = path_match.group(1)
                
        elif command_type == "write":
            command_info["action"] = "write"
            path_match = re.search(r'path="([^"]*)"', command_xml)
            if path_match:
                command_info["path"] = path_match.group(1)
            
            # Extract content
            content_match = re.search(r'<write[^>]*>(.*?)</write>', command_xml, re.DOTALL)
            if content_match:
                command_info["content"] = content_match.group(1).strip()
                
        elif command_type == "list":
            command_info["action"] = "list"
            path_match = re.search(r'path="([^"]*)"', command_xml)
            if path_match:
                command_info["path"] = path_match.group(1)
                
        elif command_type == "search":
            command_info["action"] = "search"
            path_match = re.search(r'path="([^"]*)"', command_xml)
            if path_match:
                command_info["path"] = path_match.group(1)
            
            pattern_match = re.search(r'pattern="([^"]*)"', command_xml)
            if pattern_match:
                command_info["pattern"] = pattern_match.group(1)
                
        elif command_type == "grep":
            command_info["action"] = "grep"
            path_match = re.search(r'path="([^"]*)"', command_xml)
            if path_match:
                command_info["path"] = path_match.group(1)
            
            pattern_match = re.search(r'pattern="([^"]*)"', command_xml)
            if pattern_match:
                command_info["pattern"] = pattern_match.group(1)
                
        elif command_type == "pwd":
            command_info["action"] = "pwd"
    
    return command_info


def mock_filesystem_request(request_url: str, json_data: Dict[str, Any] = None) -> MockResponse:
    """
    Mock filesystem API requests to simulate server responses.
    
    Args:
        request_url: The URL being requested
        json_data: The request payload
        
    Returns:
        Mock response object
    """
    json_data = json_data or {}
    
    # Mock different API endpoints
    if "/read_file" in request_url:
        path = json_data.get("path", "")
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r") as f:
                content = f.read()
            return MockResponse({"content": content, "path": path})
        return MockResponse({"error": "File not found"}, 404)
        
    elif "/write_file" in request_url:
        path = json_data.get("path", "")
        content = json_data.get("content", "")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return MockResponse({"success": True, "path": path})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/list_directory" in request_url:
        path = json_data.get("path", "")
        try:
            entries = []
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                entry_info = {
                    "name": entry,
                    "path": entry_path,
                    "type": "directory" if os.path.isdir(entry_path) else "file",
                    "size": os.path.getsize(entry_path) if os.path.isfile(entry_path) else None,
                }
                entries.append(entry_info)
            return MockResponse({"entries": entries, "path": path})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/search_files" in request_url:
        import glob
        path = json_data.get("path", "")
        pattern = json_data.get("pattern", "")
        try:
            search_pattern = os.path.join(path, pattern)
            matches = glob.glob(search_pattern, recursive=True)
            return MockResponse({"matches": matches})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/grep_search" in request_url:
        path = json_data.get("path", "")
        pattern = json_data.get("pattern", "")
        try:
            matches = []
            for root, dirs, files in os.walk(path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r') as f:
                            for i, line in enumerate(f, 1):
                                if pattern in line:
                                    matches.append({
                                        "file": filepath,
                                        "line": str(i),
                                        "content": line.strip()
                                    })
                    except:
                        pass
            return MockResponse({"matches": matches})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/pwd" in request_url:
        return MockResponse({"current_dir": os.getcwd()})
        
    elif "/list_allowed_directories" in request_url:
        return MockResponse({"allowed_directories": ["/home/dago/dev/projects/llm"]})
        
    # Default response for unhandled endpoints
    return MockResponse({"error": "Endpoint not supported"}, 404)


def patch_filesystem_api(func):
    """
    Decorator to patch filesystem API calls.
    
    Args:
        func: The test function to decorate
        
    Returns:
        Decorated function with patched API calls
    """
    @patch('requests.post', side_effect=lambda url, json=None, **kwargs: mock_filesystem_request(url, json))
    @patch('requests.get', side_effect=lambda url, **kwargs: mock_filesystem_request(url))
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper