"""
Contract tests to ensure test mocks stay synchronized with actual implementations.

These tests verify that our test mocks correctly implement the same interface
as the real components they're mocking, preventing tests from becoming decoupled
from source code as the project evolves.
"""

import inspect
import sys
import os

# Add project root to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.mcp.mcp_command_handler import MCPCommandHandler
from src.utils.xml_parser import StreamingXMLParser

# Import our test mocks
from tests.e2e.mcp_filesystem.test_mcp_filesystem_e2e import (
    MockMCPCommandHandler,
    MockStreamingXMLParser,
)


def test_mock_command_handler_interface():
    """Verify that MockMCPCommandHandler implements the same interface as the real MCPCommandHandler."""
    # Get public methods from real command handler
    real_methods = {
        name
        for name, obj in inspect.getmembers(MCPCommandHandler)
        if not name.startswith("_") and callable(obj)
    }

    # Get public methods from mock command handler
    mock_methods = {
        name
        for name, obj in inspect.getmembers(MockMCPCommandHandler)
        if not name.startswith("_") and callable(obj)
    }

    # Essential methods that must be implemented
    essential_methods = {
        "extract_file_commands",
        "execute_file_commands",
        "format_command_results",
        "process_streaming_response",
    }

    # Verify essential methods exist in mock
    missing_methods = essential_methods - mock_methods
    assert not missing_methods, f"Mock is missing essential methods: {missing_methods}"

    # Report on other methods that might be useful to implement
    other_methods = (
        real_methods - essential_methods - {"__init__", "__dict__", "__weakref__"}
    )
    other_missing = other_methods - mock_methods
    if other_missing:
        print(
            f"Note: Mock could implement these non-essential methods: {other_missing}"
        )


def test_mock_parser_interface():
    """Verify that MockStreamingXMLParser implements the same interface as StreamingXMLParser."""
    # Get public methods from real parser
    real_methods = {
        name
        for name, obj in inspect.getmembers(StreamingXMLParser)
        if not name.startswith("_") and callable(obj)
    }

    # Get public methods from mock parser
    mock_methods = {
        name
        for name, obj in inspect.getmembers(MockStreamingXMLParser)
        if not name.startswith("_") and callable(obj)
    }

    # Essential methods that must be implemented
    essential_methods = {"feed", "get_command", "reset"}

    # Verify essential methods exist in mock
    missing_methods = essential_methods - mock_methods
    assert not missing_methods, f"Mock is missing essential methods: {missing_methods}"


def test_command_extraction_parity():
    """Verify that the mock command handler extracts commands correctly."""
    # Sample command to test
    sample_command = """<mcp:filesystem>
    <read path="/test/path/file.txt" />
</mcp:filesystem>"""

    # Create real and mock command handlers
    real_handler = MCPCommandHandler("TEST_AGENT")
    mock_handler = MockMCPCommandHandler("TEST_AGENT")

    # Extract commands with both handlers
    real_result = real_handler.extract_file_commands(sample_command)
    mock_result = mock_handler.extract_file_commands(sample_command)

    # Check that they both extracted the same action and path
    assert len(real_result) == len(mock_result), (
        "Different number of commands extracted"
    )

    if real_result and mock_result:
        assert real_result[0]["action"] == mock_result[0]["action"], (
            "Different actions extracted"
        )
        assert real_result[0]["path"] == mock_result[0]["path"], (
            "Different paths extracted"
        )


def test_basic_filesystem_command_formats():
    """Test that our basic filesystem command formats are handled correctly."""
    # Test cases for different command formats
    test_cases = [
        # read command
        (
            '<mcp:filesystem><read path="/test/file.txt" /></mcp:filesystem>',
            {"action": "read", "path": "/test/file.txt"},
        ),
        # write command
        (
            '<mcp:filesystem><write path="/test/file.txt">Test content</write></mcp:filesystem>',
            {"action": "write", "path": "/test/file.txt", "content": "Test content"},
        ),
        # list command
        (
            '<mcp:filesystem><list path="/test/dir" /></mcp:filesystem>',
            {"action": "list", "path": "/test/dir"},
        ),
        # search command
        (
            '<mcp:filesystem><search path="/test/dir" pattern="*.py" /></mcp:filesystem>',
            {"action": "search", "path": "/test/dir", "pattern": "*.py"},
        ),
        # grep command
        (
            '<mcp:filesystem><grep path="/test/dir" pattern="def test" /></mcp:filesystem>',
            {"action": "grep", "path": "/test/dir", "pattern": "def test"},
        ),
        # cd command
        (
            '<mcp:filesystem><cd path="/test/dir" /></mcp:filesystem>',
            {"action": "cd", "path": "/test/dir"},
        ),
    ]

    # Set up handlers
    mock_handler = MockMCPCommandHandler("TEST_AGENT")

    # Test each case
    for command_xml, expected in test_cases:
        commands = mock_handler.extract_file_commands(command_xml)
        assert len(commands) == 1, f"Expected to extract one command from {command_xml}"
        cmd = commands[0]

        # Check action
        assert cmd["action"] == expected["action"], (
            f"Action mismatch: got {cmd['action']}, expected {expected['action']}"
        )

        # Check path if present
        if "path" in expected:
            assert cmd["path"] == expected["path"], (
                f"Path mismatch: got {cmd.get('path')}, expected {expected['path']}"
            )

        # Check content if present
        if "content" in expected:
            assert cmd.get("content") == expected["content"], f"Content mismatch"

        # Check pattern if present
        if "pattern" in expected:
            assert cmd.get("pattern") == expected["pattern"], f"Pattern mismatch"

