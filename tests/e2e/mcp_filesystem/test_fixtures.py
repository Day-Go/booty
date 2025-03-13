"""
Test fixtures specifically for MCP filesystem end-to-end tests.

These fixtures help with test-source coupling by:
1. Providing shared test fixtures
2. Automatically detecting source API changes
3. Creating adaptable tests that are resilient to minor implementation changes
"""

import pytest
import os
import sys
import inspect
import functools
import re
import builtins
from typing import Callable, Dict, Any, Set, List, Optional
from unittest.mock import patch

# Add project root to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.mcp_filesystem_client import MCPFilesystemClient
from src.mcp_command_handler import MCPCommandHandler
from src.xml_parser import StreamingXMLParser

from tests.e2e.mcp_filesystem.test_helpers import mock_filesystem_request


@pytest.fixture
def mock_project_path():
    """Return the path to the mock project for tests."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_project"))


@pytest.fixture
def temp_mock_project(tmp_path):
    """Create a temporary copy of the mock project for tests that modify files."""
    import shutil
    mock_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_project"))
    temp_project = tmp_path / "mock_project"
    shutil.copytree(mock_project_path, temp_project)
    return temp_project


@pytest.fixture
def patched_filesystem():
    """Patch filesystem API requests for tests."""
    with patch('requests.post', side_effect=lambda url, json=None, **kwargs: mock_filesystem_request(url, json)), \
         patch('requests.get', side_effect=lambda url, **kwargs: mock_filesystem_request(url)):
        yield


def get_public_class_methods(cls) -> Set[str]:
    """Get all public method names from a class."""
    return {name for name, _ in inspect.getmembers(cls, inspect.ismethod) 
            if not name.startswith('_')}


def resilient_e2e_test(real_components: List[Any] = None, auto_patch: bool = True):
    """
    Decorator for E2E tests to make them more resilient to API changes.
    
    This decorator:
    1. Validates that required real components exist
    2. Patches filesystem API calls if needed
    3. Provides graceful degradation if API changes
    
    Args:
        real_components: List of real component classes to validate against
        auto_patch: Whether to automatically patch filesystem API calls
    """
    real_components = real_components or [MCPCommandHandler, StreamingXMLParser, MCPFilesystemClient]
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if required real components have changed
            component_methods = {}
            for component in real_components:
                component_methods[component.__name__] = get_public_class_methods(component)
            
            # Track which API methods the test actually uses
            used_methods = set()
            original_getattr = builtins.__dict__['__getattribute__']
            
            def tracking_getattr(obj, name, *args, **kwargs):
                result = original_getattr(obj, name, *args, **kwargs)
                # Track method calls on our components
                if hasattr(obj, '__class__') and obj.__class__.__name__ in component_methods:
                    if name in component_methods[obj.__class__.__name__]:
                        used_methods.add(f"{obj.__class__.__name__}.{name}")
                return result
            
            # Apply patches if needed
            patches = []
            if auto_patch:
                post_patch = patch('requests.post', side_effect=lambda url, json=None, **kwargs: mock_filesystem_request(url, json))
                get_patch = patch('requests.get', side_effect=lambda url, **kwargs: mock_filesystem_request(url))
                post_patch.start()
                get_patch.start()
                patches.extend([post_patch, get_patch])
            
            # Add attribute tracking for analysis (optional for performance)
            # builtins.__dict__['__getattribute__'] = tracking_getattr
            
            try:
                # Run the actual test
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # If the test fails, check if it's due to API changes
                if any(re.search(r'has no attribute', str(e)) for component in component_methods
                       for method in component_methods[component]):
                    # Detect which method might be missing
                    missing_method_match = re.search(r"'([^']+)' object has no attribute '([^']+)'", str(e))
                    if missing_method_match:
                        obj_type, missing_method = missing_method_match.groups()
                        print(f"Test failing due to API change: {obj_type}.{missing_method} is now missing")
                        print(f"Consider updating tests to match current API")
                # Re-raise the exception
                raise
            finally:
                # Clean up patches
                for p in patches:
                    p.stop()
                # Restore original getattr
                # builtins.__dict__['__getattribute__'] = original_getattr
        
        return wrapper
    
    return decorator