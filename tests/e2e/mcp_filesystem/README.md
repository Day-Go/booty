# MCP Filesystem End-to-End Tests

This directory contains end-to-end tests for the MCP filesystem functionality. The tests simulate a conversation with an agent that uses MCP commands to interact with the filesystem.

## Test Structure

- `test_mcp_filesystem_e2e.py`: Main test file containing the end-to-end tests
- `conftest.py`: Pytest fixtures specific to MCP filesystem testing
- `mock_project/`: A mock Python project structure used as a test environment

## Mock Project Structure

The `mock_project/` directory contains:

- `src/`: Application source code
- `database/`: Database models and connection utilities
- `services/`: Service implementations
- `tests/`: Project test files
- `config/`: Configuration files
- `docs/`: Documentation
- Various configuration files like `requirements.txt`, `.env.example`, etc.

## Tests Included

1. **File Reading**: Tests reading files using MCP commands
2. **File Writing**: Tests creating and modifying files
3. **Directory Listing**: Tests listing directory contents
4. **File Searching**: Tests finding files using patterns
5. **Content Searching**: Tests grepping file contents
6. **Code Block Command Parsing**: Tests MCP commands inside markdown code blocks
7. **Agent Continuation**: Tests that agents continue properly after MCP command execution
8. **Full Conversation Simulation**: Tests a complete multi-turn conversation with various MCP commands

## Running the Tests

```bash
# Run all MCP filesystem tests
pytest tests/e2e/mcp_filesystem/

# Run a specific test
pytest tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py::TestMCPFilesystemE2E::test_read_file_command

# Run with more verbosity
pytest tests/e2e/mcp_filesystem/ -v
```

## Requirements

The tests require:

1. A running MCP filesystem server (started automatically by the test fixtures)
2. The Python packages defined in the project's requirements.txt

## Test Design

Each test follows this general pattern:

1. Set up the test environment
2. Create a simulated agent response with MCP commands
3. Process the response token-by-token to detect commands
4. Execute the commands and verify results
5. Check for correct agent continuation after command execution