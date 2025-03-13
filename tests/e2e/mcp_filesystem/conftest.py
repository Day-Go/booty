"""
Test fixtures for MCP filesystem e2e tests
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)


class MockResponse:
    """Mock response for requests"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")


# Patch the requests.post method for testing
def mock_post(*args, **kwargs):
    """Mock implementation of requests.post"""
    url = args[0]
    json_data = kwargs.get('json', {})
    
    if "/read_file" in url:
        file_path = json_data.get("path", "")
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                return MockResponse({"content": content, "path": file_path})
            else:
                return MockResponse({"error": "File not found"}, 404)
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/write_file" in url:
        file_path = json_data.get("path", "")
        content = json_data.get("content", "")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(content)
            return MockResponse({"success": True, "path": file_path})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/list_directory" in url:
        dir_path = json_data.get("path", "")
        try:
            entries = []
            for entry in os.listdir(dir_path):
                entry_path = os.path.join(dir_path, entry)
                entry_info = {
                    "name": entry,
                    "path": entry_path,
                    "type": "directory" if os.path.isdir(entry_path) else "file",
                    "size": os.path.getsize(entry_path) if os.path.isfile(entry_path) else None,
                }
                entries.append(entry_info)
            return MockResponse({"entries": entries, "path": dir_path})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/search_files" in url:
        import glob
        dir_path = json_data.get("path", "")
        pattern = json_data.get("pattern", "")
        try:
            search_pattern = os.path.join(dir_path, pattern)
            matches = glob.glob(search_pattern, recursive=True)
            return MockResponse({"matches": matches})
        except Exception as e:
            return MockResponse({"error": str(e)}, 500)
            
    elif "/grep_search" in url:
        import re
        dir_path = json_data.get("path", "")
        pattern = json_data.get("pattern", "")
        try:
            matches = []
            # Simple mock implementation of grep
            for root, dirs, files in os.walk(dir_path):
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
    
    return MockResponse({"message": "Endpoint not mocked"}, 404)


# Patch the requests.get method for testing
def mock_get(*args, **kwargs):
    """Mock implementation of requests.get"""
    url = args[0]
    
    if "/pwd" in url:
        return MockResponse({"current_dir": os.getcwd()})
        
    elif "/list_allowed_directories" in url:
        return MockResponse({"allowed_directories": ["/home/dago/dev/projects/llm"]})
    
    return MockResponse({"message": "Endpoint not mocked"}, 404)


@pytest.fixture(scope="session")
def mcp_server():
    """Mock MCP server for testing"""
    # No real server is started, we just patch the requests library
    with patch('requests.post', side_effect=mock_post), \
         patch('requests.get', side_effect=mock_get):
        yield "http://127.0.0.1:8000"  # Return a dummy URL


@pytest.fixture(scope="session")
def mock_project_path():
    """Return the path to the mock project for tests"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_project"))


@pytest.fixture
def temp_workspace():
    """Create a temporary working directory for tests that modify files"""
    # Create a temp directory
    temp_dir = tempfile.mkdtemp()
    
    # Copy the mock project to the temp directory
    mock_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_project"))
    temp_project_path = os.path.join(temp_dir, "mock_project")
    shutil.copytree(mock_project_path, temp_project_path)
    
    yield temp_project_path
    
    # Clean up after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def mcp_fs_client():
    """Create an MCP filesystem client for tests"""
    from src.mcp_filesystem_client import MCPFilesystemClient
    return MCPFilesystemClient(base_url="http://127.0.0.1:8000")


@pytest.fixture
def xml_parser():
    """Create an XML parser for tests"""
    from src.xml_parser import StreamingXMLParser
    return StreamingXMLParser(debug_mode=False)


@pytest.fixture
def mcp_command_handler():
    """Create an MCP command handler for tests"""
    from src.mcp_command_handler import MCPCommandHandler
    return MCPCommandHandler(agent_id="TEST_AGENT")