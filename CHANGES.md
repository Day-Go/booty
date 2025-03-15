# CHANGES

## 2025-03-15

### XML Parser Fix for MCP Commands
- Fixed critical bug in StreamingXMLParser.check_for_mcp_commands() that prevented proper detection of MCP commands during streaming
- Improved buffer management to correctly track processed XML content
- Prevented duplicate processing and XML structure mismatches by tracking processed portions of the buffer
- Ensured proper handling of XML tags arriving in different chunks during streaming
- Fixed the tag stack management to correctly match opening and closing tags
- Also fixed a related indentation issue in mcp_command_handler.py that was causing syntax errors

## 2025-03-15

### MCP Filesystem Update
- Replaced duplicate MCPFilesystemClient implementation in ollama_inference_offline.py with import from mcp_filesystem_client.py
- Added XML command parsing capabilities to OfflineFileAgent, matching mcp_command_handler.py
- Improved error handling and formatting of command results
- Added support for all MCP filesystem commands (read, write, list, search, cd, pwd, grep, mkdir)
- Fixed critical TODO item: "The contents of this folder is out of date and no longer reflects how the filesystem mcp commands are formatter, and how the server/clients are implemented"