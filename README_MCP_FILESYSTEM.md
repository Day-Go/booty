# MCP Filesystem Server with XML Interface

This README explains how to set up and use the Model Control Protocol (MCP) Filesystem Server implementation with its XML-based command interface.

## Prerequisites

Ensure you have the following installed on your system:

```bash
sudo pacman -S python python-pip
pip install fastapi uvicorn pydantic requests
```

## Starting the MCP Filesystem Server

1. Navigate to the project directory:
```bash
cd /home/dago/dev/projects/llm
```

2. Start the MCP Filesystem Server:
```bash
python src/mcp_filesystem_server.py
```

This will launch the server on `http://127.0.0.1:8000`. The server provides a REST API for filesystem operations.

## XML Command Format

The MCP Filesystem interface now uses an XML-based syntax for all commands. Commands should be wrapped in `<mcp:filesystem>` tags:

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
| pwd | `<pwd />` | Get current working directory |
| grep | `<grep path="/path" pattern="pattern" />` | Search file contents for pattern |

## API Endpoints

The following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/read_file` | POST | Read a file from the filesystem |
| `/write_file` | POST | Write content to a file |
| `/list_directory` | POST | List contents of a directory |
| `/create_directory` | POST | Create a directory |
| `/search_files` | POST | Search files with glob pattern |
| `/grep_search` | POST | Search file contents using grep |
| `/pwd` | GET | Get current working directory |
| `/list_allowed_directories` | GET | Get list of allowed paths |

## Using the Clients

There are two client implementations:

### 1. Ollama Integration Client

The `ollama_inference.py` integrates with both Ollama API and the MCP Filesystem Server. This requires:

1. Start Ollama server:
```bash
ollama serve
```

2. Start MCP Filesystem server (in a separate terminal):
```bash
python src/mcp_filesystem_server.py
```

3. Start the Ollama inference client (in a third terminal):
```bash
python src/ollama_inference.py
```

### 2. Offline Client (No Ollama Required)

The `ollama_inference_offline.py` only connects to the MCP Filesystem Server and doesn't need Ollama running. This is useful for testing file operations without an LLM:

1. Start MCP Filesystem server:
```bash
python src/mcp_filesystem_server.py
```

2. Start the offline client (in a separate terminal):
```bash
python src/ollama_inference_offline.py
```

## Usage Examples

Once the MCP server and either client are running, you can use the following XML commands:

### Basic Operations

1. List directory contents:
```xml
<mcp:filesystem>
    <list path="/home/dago/dev/projects/llm" />
</mcp:filesystem>
```

2. Read a file:
```xml
<mcp:filesystem>
    <read path="/home/dago/dev/projects/llm/CLAUDE.md" />
</mcp:filesystem>
```

3. Search for files (using glob pattern):
```xml
<mcp:filesystem>
    <search path="/home/dago/dev/projects/llm/src" pattern="*.py" />
</mcp:filesystem>
```

4. Search file contents (using grep):
```xml
<mcp:filesystem>
    <grep path="/home/dago/dev/projects/llm/src" pattern="import" />
</mcp:filesystem>
```

5. Get current working directory:
```xml
<mcp:filesystem>
    <pwd />
</mcp:filesystem>
```

6. Write to a file:
```xml
<mcp:filesystem>
    <write path="/home/dago/dev/projects/llm/test_output.txt">
        This content will be written to the file.
        Multiple lines are supported.
    </write>
</mcp:filesystem>
```

### Practical Examples

1. Multiple commands in a single block:
```xml
<mcp:filesystem>
    <pwd />
    <list path="/home/dago/dev/projects/llm" />
    <grep path="/home/dago/dev/projects/llm/src" pattern="import requests" />
</mcp:filesystem>
```

2. Read multiple files:
```xml
<mcp:filesystem>
    <read path="/home/dago/dev/projects/llm/src/ollama_inference.py" />
    <read path="/home/dago/dev/projects/llm/src/mcp_filesystem_server.py" />
</mcp:filesystem>
```

3. Create project structure and write files:
```xml
<mcp:filesystem>
    <list path="/home/dago/dev/projects/llm" />
    <write path="/home/dago/dev/projects/llm/notes.md">
        # Project Notes
        
        This document contains notes about the project structure.
    </write>
</mcp:filesystem>
```

## Advantages of XML Format

The XML-based command format provides several benefits:

1. **Structured Data**: Clear hierarchy and organization of command components
2. **Better Parsing**: Reliable parsing with proper XML libraries
3. **Multi-line Content**: Native support for multi-line content in write operations
4. **Parameter Clarity**: Attributes clearly define parameters for each command
5. **Extensibility**: Easy to extend with new commands or parameters
6. **Nested Operations**: Support for grouped commands in a single block
7. **Reduced Ambiguity**: Explicit start and end tags eliminate parsing ambiguities

## Security Notes

- The server restricts file operations to allowed directories specified in `ALLOWED_DIRECTORIES`
- All paths are validated to prevent directory traversal attacks
- File operations are logged for auditing purposes

## Troubleshooting

- If the `ollama_inference.py` client fails with a connection error to port 11434, Ollama is not running
- If file operations fail with a connection error to port 8000, the MCP server is not running
- Try the offline client first to validate MCP server functionality
- Check permissions for file operations in the allowed directories
- The offline client is useful for testing and debugging without Ollama dependencies

---

This implementation provides a robust filesystem interface for language models via the MCP protocol with an XML-based command structure, allowing controlled access to the filesystem while maintaining security boundaries and improving parsing reliability.

## Testing the MCP Filesystem

The MCP Filesystem components are covered by comprehensive tests, including end-to-end tests and contract tests. See the `/tests/e2e/mcp_filesystem/` directory for test implementations.

### Test-Source Coupling

To ensure tests remain synchronized with the MCP Filesystem implementation:

1. **Contract Tests**: Tests in `/tests/e2e/mcp_filesystem/test_contract_coupling.py` verify that mock implementations match real implementations
2. **Automated Updates**: When MCP Filesystem code changes, run `python /tools/update_mocks.py` to update mock implementations
3. **Pre-commit Verification**: Git hooks ensure tests are synchronized with source code before committing

For detailed information on the test-source coupling framework, see [/tests/TEST_COUPLING.md](/tests/TEST_COUPLING.md).