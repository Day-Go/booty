"""Pytest configuration file for the LLM project."""

import os
import sys
import pytest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define shared fixtures here if needed
@pytest.fixture
def sample_mcp_commands():
    """Return a set of sample MCP commands for testing."""
    return {
        "read": "<mcp:filesystem><read path='/path/to/file.txt' /></mcp:filesystem>",
        "write": "<mcp:filesystem><write path='/path/to/file.txt'>Test content</write></mcp:filesystem>",
        "list": "<mcp:filesystem><list path='/path/to/dir' /></mcp:filesystem>",
        "search": "<mcp:filesystem><search path='/path/to/dir' pattern='*.py' /></mcp:filesystem>",
        "grep": "<mcp:filesystem><grep path='/path/to/dir' pattern='search term' /></mcp:filesystem>",
        "pwd": "<mcp:filesystem><pwd /></mcp:filesystem>",
        "complex": "<mcp:filesystem><read path='/path/to/file.txt' /><list path='/path' /><grep path='/src' pattern='function' /></mcp:filesystem>"
    }