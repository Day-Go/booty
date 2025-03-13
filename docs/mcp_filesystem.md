# Filesystem MCP Server

## XML-Based Interface

The MCP Filesystem Server now uses an XML-based interface for more robust and flexible command processing. All filesystem operations are specified using XML syntax, which provides better parsing reliability and extensibility compared to the previous command-line style format.

## Command Format

All MCP filesystem commands should be wrapped in `<mcp:filesystem>` tags and use proper XML syntax:

```xml
<mcp:filesystem>
    <command attribute="value" attribute2="value2" />
</mcp:filesystem>
```

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

### pwd

Get current working directory.

```xml
<mcp:filesystem>
    <pwd />
</mcp:filesystem>
```

### grep

Search file contents using pattern matching.

```xml
<mcp:filesystem>
    <grep path="/absolute/path/to/search" pattern="grep-pattern" />
</mcp:filesystem>
```

## API Details

### Resources
file://system: File system operations interface

### Tools

#### read_file
Read complete contents of a file
- Input: path (string)
- Reads complete file contents with UTF-8 encoding

#### read_multiple_files
Read multiple files simultaneously
- Input: paths (string[])
- Failed reads won't stop the entire operation

#### write_file
Create new file or overwrite existing (exercise caution with this)
- Inputs:
  - path (string): File location
  - content (string): File content

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
- Succeeds silently if directory exists

#### list_directory
List directory contents with [FILE] or [DIR] prefixes
- Input: path (string)

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