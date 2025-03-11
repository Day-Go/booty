# MCP Filesystem Server for Arch Linux

This README explains how to set up and use the Model Control Protocol (MCP) Filesystem Server implementation for Arch Linux environments.

## Prerequisites

Ensure you have the following installed on your Arch Linux system:

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

## API Endpoints

The following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/read_file` | POST | Read a file from the filesystem |
| `/write_file` | POST | Write content to a file |
| `/list_directory` | POST | List contents of a directory |
| `/create_directory` | POST | Create a directory |
| `/search_files` | POST | Search files with glob pattern |
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

Once the MCP server and either client are running, you can use the following commands:

### Basic Operations

1. List directory contents:
```
list directory /home/dago/dev/projects/llm
```

2. Read a file:
```
read file /home/dago/dev/projects/llm/CLAUDE.md
```

3. Search for files:
```
search for "*.py" in /home/dago/dev/projects/llm/src
```

4. Write to a file:
```
write to file /home/dago/dev/projects/llm/test_output.txt with content
```

### Practical Examples

1. Summarize a Python file:
```
read file /home/dago/dev/projects/llm/src/ollama_inference.py and summarize its main functionality
```

2. Find all Python files and analyze imports:
```
search for "*.py" in /home/dago/dev/projects/llm and list the main imports used in each file
```

3. Create project structure:
```
list directory /home/dago/dev/projects/llm and suggest improvements to the project structure
```

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

This implementation provides a minimal but functional filesystem interface for language models via the MCP protocol, allowing controlled access to the filesystem while maintaining security boundaries.