# MCP Filesystem Module

This module provides a filesystem interface for LLM agents via the Model Control Protocol (MCP). It allows agents to interact with the local filesystem in a secure and structured way, with contextual awareness of their directory location.

## Overview

The MCP Filesystem is a key component of the hierarchical multi-agent system that allows agents to:

- Navigate the filesystem with directory context awareness
- Read and write files with proper error handling
- Search for files and content using patterns
- Maintain context about their location in the filesystem
- Execute multiple commands in sequence

## Core Components

### Server (`mcp_filesystem_server.py`)

The server component exposes HTTP endpoints that the client can call to perform filesystem operations:

- Runs as a FastAPI server on localhost:8000
- Tracks the current working directory context
- Validates file paths for security
- Provides detailed error messages for operations
- Supports a wide range of filesystem operations

### Client (`mcp_filesystem_client.py`)

The client component is used by agents to interact with the server:

- Formats requests to the server
- Handles error responses gracefully
- Provides pretty-printed console output of operations
- Exposes a simple API for all filesystem operations

## Deployment & Execution

### Automatic Execution

The MCP Filesystem server starts automatically when running `main.py`:

```bash
python src/main.py
```

This launches the server in a background thread at startup, making it immediately available to the agent.

### Standalone Execution

For testing or development purposes, you can run the server directly:

```bash
python src/mcp_filesystem_server.py
```

This is useful for:
- Testing MCP functionality without the full agent system
- Debugging server behavior
- Working with custom client implementations

## Integration in Agent Code

To use the MCP Filesystem in your agent code:

```python
# Initialize the client
from src.mcp_filesystem_client import MCPFilesystemClient
mcp_fs = MCPFilesystemClient(base_url="http://127.0.0.1:8000")

# Get working directory information
working_dir_info = mcp_fs.get_working_directory()

# List directory contents
contents = mcp_fs.list_directory("/path/to/directory")

# Read a file
file_content = mcp_fs.read_file("/path/to/file.txt")

# Change directory
mcp_fs.change_directory("/new/working/directory")

# Write to a file
mcp_fs.write_file("/path/to/file.txt", "File content")
```

## XML Command Format

Agents use an XML-based syntax to interact with the filesystem. All commands are wrapped in `<mcp:filesystem>` tags:

```xml
<mcp:filesystem>
    <command attribute="value" attribute2="value2" />
</mcp:filesystem>
```

### Available Commands

| Command | Format | Description |
|---------|--------|-------------|
| read | `<read path="/path/to/file" />` | Read a file's contents |
| write | `<write path="/path/to/file">Content</write>` | Write content to a file |
| list | `<list path="/path/to/directory" />` | List directory contents |
| search | `<search path="/path" pattern="pattern" />` | Search for files matching pattern |
| cd | `<cd path="/path/to/directory" />` | Change working directory |
| get_working_directory | `<get_working_directory />` | Get current and script directories |
| grep | `<grep path="/path" pattern="pattern" />` | Search file contents for pattern |
| create_directory | `<create_directory path="/path/to/dir" />` | Create a new directory |

## Directory Context Awareness

The MCP Filesystem maintains two important directory contexts:

1. **Current Working Directory**: Initially set to the directory from which the script was launched. Can be changed using the `cd` command.
2. **Script Directory**: Fixed location of the server script, useful for finding project-relative paths.

This allows agents to:
- Understand where they are in the filesystem
- Navigate between directories while maintaining context
- Use relative paths effectively
- Reference project files regardless of the current directory

## Error Handling

The MCP Filesystem provides detailed error messages for operations that fail:

- Specific HTTP status codes (404, 403, etc.)
- Descriptive error messages explaining what went wrong
- Context about the failed operation

Error types include:
- File not found (404)
- Permission denied (403)
- Invalid path or argument (400)
- Binary content in text files (422)
- Server errors (500)

## Security Considerations

The system includes security measures to prevent unauthorized access:

- Path validation to restrict access to allowed directories
- Detailed permission checking for all operations
- Safe handling of file operations
- Prevention of directory traversal attacks

## Testing

The MCP Filesystem components are covered by comprehensive tests:

- End-to-end tests in `/tests/e2e/mcp_filesystem/`
- Contract tests ensuring mock implementations match real behavior
- Automated test updating tools in `/tools/update_mocks.py`

For detailed information on the test-source coupling framework, see `/tests/TEST_COUPLING.md`.

## API Documentation

For more detailed documentation on available commands and best practices, see:
- `/docs/mcp_filesystem.md` - Full API documentation
- `/docs/mcp_agent_system_prompt.md` - System prompt for agents using the MCP Filesystem