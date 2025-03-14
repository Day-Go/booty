# Filesystem MCP Server

## Overview

The MCP Filesystem Server provides a robust and flexible way for LLM agents to interact with the local filesystem. It offers a contextualized file system navigation experience where the agent:

1. Knows the directory from which the script was launched
2. Can navigate the filesystem using standard commands like `cd`
3. Maintains directory context across multiple commands
4. Receives detailed error messages when operations fail

## XML-Based Interface

The MCP Filesystem Server uses an XML-based interface for command processing. All filesystem operations are specified using XML syntax, which provides better parsing reliability and extensibility compared to command-line style formats.

## Command Format

All MCP filesystem commands should be wrapped in `<mcp:filesystem>` tags and use proper XML syntax:

```xml
<mcp:filesystem>
    <command attribute="value" attribute2="value2" />
</mcp:filesystem>
```

## Directory Context

The server maintains two important directory contexts:

1. **Current Working Directory**: The directory from which the script was launched, which can be changed using the `cd` command.
2. **Script Directory**: The fixed directory containing the server script, useful for finding project-relative paths.

This allows the agent to navigate the filesystem naturally, similar to a command-line shell, while maintaining awareness of the project's location.

## Available Commands

### read

Read complete contents of a file with UTF-8 encoding.

```xml
<mcp:filesystem>
    <read path="/absolute/path/to/file" />
</mcp:filesystem>
```

### write

Create new file or overwrite existing file.

```xml
<mcp:filesystem>
    <write path="/absolute/path/to/file">
        Content to write to the file goes here.
        Can be multi-line content.
    </write>
</mcp:filesystem>
```

### list

List directory contents.

```xml
<mcp:filesystem>
    <list path="/absolute/path/to/directory" />
</mcp:filesystem>
```

### search

Recursively search for files/directories.

```xml
<mcp:filesystem>
    <search path="/absolute/path/to/search" pattern="search-pattern" />
</mcp:filesystem>
```

### cd

Change the current working directory.

```xml
<mcp:filesystem>
    <cd path="/absolute/path/to/directory" />
</mcp:filesystem>
```

The MCP Filesystem server tracks the directory from which the script was launched. The current working directory can be changed using the `cd` command and is maintained across commands. This allows the agent to navigate the filesystem in a natural way, similar to a command-line shell.

### get_working_directory

Get the current working directory and script directory.

```xml
<mcp:filesystem>
    <get_working_directory />
</mcp:filesystem>
```

This command returns both the current working directory (which changes when you use `cd`) and the script directory (which is fixed and indicates where the server script is located).

### grep

Search file contents using pattern matching.

```xml
<mcp:filesystem>
    <grep path="/absolute/path/to/search" pattern="grep-pattern" />
</mcp:filesystem>
```

## Error Handling

The MCP Filesystem server now provides comprehensive and descriptive error messages. Errors are returned with appropriate HTTP status codes and detailed messages explaining the cause of the error.

Common error cases include:

- **404 Not Found**: File or directory doesn't exist
- **403 Forbidden**: Permission denied or path outside allowed directories
- **400 Bad Request**: Invalid path or operation (e.g., attempting to read a directory as a file)
- **422 Unprocessable Entity**: File contains binary content that can't be read as text
- **500 Internal Server Error**: Unexpected errors with detailed explanation

## API Details

### Resources
file://system: File system operations interface

### Tools

#### read_file
Read complete contents of a file
- Input: path (string)
- Reads complete file contents with UTF-8 encoding
- Error cases: File not found, path is not a file, permission denied, binary content

#### read_multiple_files
Read multiple files simultaneously
- Input: paths (string[])
- Failed reads won't stop the entire operation

#### write_file
Create new file or overwrite existing (exercise caution with this)
- Inputs:
  - path (string): File location
  - content (string): File content
- Creates parent directories if needed
- Error cases: Path exists as directory, permission denied, parent directory not writable

#### edit_file
Make selective edits using advanced pattern matching and formatting
- Features:
  - Line-based and multi-line content matching
  - Whitespace normalization with indentation preservation
  - Fuzzy matching with confidence scoring
  - Multiple simultaneous edits with correct positioning
  - Indentation style detection and preservation
  - Git-style diff output with context
  - Preview changes with dry run mode
  - Failed match debugging with confidence scores
- Inputs:
  - path (string): File to edit
  - edits (array): List of edit operations
  - oldText (string): Text to search for (can be substring)
  - newText (string): Text to replace with
  - dryRun (boolean): Preview changes without applying (default: false)
  - options (object): Optional formatting settings
  - preserveIndentation (boolean): Keep existing indentation (default: true)
  - normalizeWhitespace (boolean): Normalize spaces while preserving structure (default: true)
  - partialMatch (boolean): Enable fuzzy matching (default: true)
- Returns detailed diff and match information for dry runs, otherwise applies changes
- Best Practice: Always use dryRun first to preview changes before applying them

#### create_directory
Create new directory or ensure it exists
- Input: path (string)
- Creates parent directories if needed
- Succeeds silently if directory already exists
- Error cases: Path exists as file, permission denied on parent directory

#### list_directory
List directory contents with file type and size information
- Input: path (string)
- Returns entries with name, path, type (file/directory), and size (for files)
- Error cases: Directory not found, path is not a directory, permission denied

#### change_directory
Change the current working directory
- Input: path (string)
- Returns previous and new directory paths
- Error cases: Directory not found, path is not a directory, permission denied
- Note: The server tracks the current working directory as a context for commands

#### get_working_directory
Get information about working directories
- No input required
- Returns:
  - current_dir: Current working directory (the path that would be seen if the agent were to run "pwd")
  - script_dir: Directory containing the server script (useful for finding project-relative paths)

#### move_file
Move or rename files and directories
- Inputs:
  - source (string)
  - destination (string)
- Fails if destination exists

#### search_files
Recursively search for files/directories
- Inputs:
  - path (string): Starting directory
  - pattern (string): Search pattern
  - excludePatterns (string[]): Exclude any patterns. Glob formats are supported.
- Case-insensitive matching
- Returns full paths to matches
- Error cases: Directory not found, path is not a directory, permission denied

#### grep_search
Search file contents using pattern matching
- Inputs:
  - path (string): Starting directory or file
  - pattern (string): Text pattern to search for
  - recursive (boolean): Whether to search recursively (default: true)
  - case_sensitive (boolean): Whether to use case-sensitive matching (default: false)
- Returns matches with file path, line number, and line content
- Error cases: Path not found, permission denied, invalid pattern

#### get_file_info
Get detailed file/directory metadata
- Input: path (string)
- Returns:
  - Size
  - Creation time
  - Modified time
  - Access time
  - Type (file/directory)
  - Permissions

#### list_allowed_directories
List all directories the server is allowed to access
- No input required
- Returns directories that this server can read/write from

## Client Features

The MCP Filesystem Client provides a robust interface for interacting with the server:

- **Error Handling**: Detailed error messages with specific error contexts
- **Request Retries**: Automatic retries for transient failures
- **Console Logging**: Colored console output for commands and responses
- **Content Preview**: Shows content previews for large files
- **Success Flags**: Consistent success/failure indicators in all responses

## Testing

The MCP Filesystem implementation includes comprehensive testing to ensure reliability and correctness. The testing framework focuses on maintaining tight coupling between tests and source code to prevent tests from becoming outdated as the codebase evolves.

### Test-Source Coupling Framework

The test-source coupling framework includes:

1. **Contract Tests**: Tests in `/tests/e2e/mcp_filesystem/test_contract_coupling.py` verify that mock implementations match real implementations, ensuring mocks used in tests accurately reflect the actual code behavior.

2. **Mock Updaters**: When the MCP Filesystem implementation changes, mock implementations are automatically updated using the tools in `/tools/update_mocks.py`.

3. **Resilient Test Fixtures**: The `resilient_e2e_test` decorator in `/tests/e2e/mcp_filesystem/test_fixtures.py` makes tests more robust against minor API changes by dynamically adapting to the current implementation.

4. **Pre-commit Verification**: Git hooks prevent committing changes that break the coupling between tests and source code.

5. **Test Dependency Analysis**: AST-based analysis identifies which tests depend on which source files, making it easier to understand the impact of code changes.

For detailed information on the test-source coupling framework, see [/tests/TEST_COUPLING.md](/tests/TEST_COUPLING.md).