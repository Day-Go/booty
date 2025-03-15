import re
from typing import Dict, List, Any

# Import existing MCPFilesystemClient and Colors
try:
    # Try relative import first (for when running as a module)
    from terminal_utils import Colors
    from mcp_filesystem_client import MCPFilesystemClient
except ImportError:
    # Fall back to absolute import (for when imported from tests)
    from src.terminal_utils import Colors
    from src.mcp_filesystem_client import MCPFilesystemClient


class OfflineFileAgent:
    """Offline version of the agent that doesn't require Ollama API"""

    def __init__(self, mcp_fs_url="http://127.0.0.1:8000", agent_id="OfflineAgent"):
        # Initialize MCP filesystem client
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        # Track tool usage
        self.tool_usage = []
        # Agent identifier for logging
        self.agent_id = agent_id
        self.debug_color = Colors.MAGENTA
        self.debug_bg_color = Colors.BG_MAGENTA

    def debug_print(self, message: str, highlight: bool = False):
        """Print a debug message with agent-specific coloring."""
        if highlight:
            print(
                f"{self.debug_bg_color}{Colors.BOLD}[{self.agent_id}] {message}{Colors.ENDC}"
            )
        else:
            print(f"{self.debug_color}[{self.agent_id}] {message}{Colors.ENDC}")

    def _extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message using XML format and fallback patterns."""
        commands = []

        # First, look for XML-formatted MCP commands
        self.debug_print("Checking for XML-formatted MCP commands")
        cleaned_message = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL)

        # Find all <mcp:filesystem> blocks in the message
        mcp_blocks = re.findall(
            r"<mcp:filesystem>(.*?)</mcp:filesystem>", cleaned_message, re.DOTALL
        )

        if mcp_blocks:
            self.debug_print(f"Found {len(mcp_blocks)} MCP filesystem blocks")

            # Process each MCP block using XML parsing
            for block_idx, block in enumerate(mcp_blocks):
                self.debug_print(f"Processing MCP block #{block_idx + 1}")

                # Wrap the block in a root element for proper XML parsing
                xml_content = f"<root>{block}</root>"

                try:
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(xml_content)

                    # Process each command element in the block
                    for cmd_element in root:
                        cmd_type = cmd_element.tag.lower()
                        self.debug_print(f"Processing command type: {cmd_type}")

                        # Convert XML elements to command dictionaries
                        if cmd_type == "read":
                            path = cmd_element.get("path", "")
                            if path:
                                self.debug_print(f"Read command with path: {path}")
                                commands.append({"action": "read", "path": path})

                        elif cmd_type == "write":
                            path = cmd_element.get("path", "")
                            content = cmd_element.text if cmd_element.text else ""
                            if path:
                                self.debug_print(f"Write command with path: {path}")
                                commands.append(
                                    {
                                        "action": "write",
                                        "path": path,
                                        "content": content,
                                    }
                                )

                        elif cmd_type == "list":
                            path = cmd_element.get("path", "")
                            if path:
                                self.debug_print(f"List command with path: {path}")
                                commands.append({"action": "list", "path": path})

                        elif cmd_type == "search":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                self.debug_print(
                                    f"Search command with path: {path}, pattern: {pattern}"
                                )
                                commands.append(
                                    {
                                        "action": "search",
                                        "path": path,
                                        "pattern": pattern,
                                    }
                                )

                        elif cmd_type == "get_working_directory" or cmd_type == "pwd":
                            self.debug_print("Working directory command")
                            commands.append({"action": "pwd"})

                        elif cmd_type == "cd" or cmd_type == "change_directory":
                            path = cmd_element.get("path", "")
                            if path:
                                self.debug_print(
                                    f"Change directory command with path: {path}"
                                )
                                commands.append({"action": "cd", "path": path})

                        elif cmd_type == "grep":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                self.debug_print(
                                    f"Grep command with path: {path}, pattern: {pattern}"
                                )
                                commands.append(
                                    {"action": "grep", "path": path, "pattern": pattern}
                                )

                        elif cmd_type == "create_directory":
                            path = cmd_element.get("path", "")
                            if path:
                                self.debug_print(
                                    f"Create directory command with path: {path}"
                                )
                                commands.append({"action": "mkdir", "path": path})

                except Exception as xml_error:
                    self.debug_print(
                        f"Error parsing XML: {str(xml_error)}", highlight=True
                    )

        # If no XML commands found, fallback to pattern matching for backward compatibility
        if not commands:
            self.debug_print(
                "No XML commands found, trying pattern matching", highlight=True
            )

            # Match patterns for file operations
            read_pattern = r"read\s+file\s+(?:from\s+)?[\"']?([^\"']+)[\"']?"
            write_pattern = (
                r"write\s+(?:to\s+)?file\s+[\"']?([^\"']+)[\"']?\s+with\s+content"
            )
            list_pattern = r"list\s+(?:directory|dir|folder)\s+[\"']?([^\"']+)[\"']?"
            search_pattern = r"search\s+(?:for\s+)?[\"']?([^\"']+)[\"']?\s+in\s+[\"']?([^\"']+)[\"']?"
            grep_pattern = (
                r"grep\s+(?:for\s+)?[\"']?([^\"']+)[\"']?\s+in\s+[\"']?([^\"']+)[\"']?"
            )
            cd_pattern = r"(?:change|cd)(?:\s+to)?\s+directory\s+[\"']?([^\"']+)[\"']?"
            pwd_pattern = (
                r"(?:pwd|print\s+working\s+directory|show\s+current\s+directory)"
            )
            mkdir_pattern = r"(?:create|make)\s+directory\s+[\"']?([^\"']+)[\"']?"

            # Extract read commands
            for match in re.finditer(read_pattern, message, re.IGNORECASE):
                path = match.group(1)
                commands.append({"action": "read", "path": path})

            # Extract write commands - note this is simplified, real impl would need to extract content too
            for match in re.finditer(write_pattern, message, re.IGNORECASE):
                path = match.group(1)
                # Try to extract content after "with content" phrase
                content_match = re.search(
                    rf"write\s+(?:to\s+)?file\s+[\"']?{re.escape(path)}[\"']?\s+with\s+content\s+(?:of\s+)?(?:[\"']([^\"']+)[\"']|(\S+))",
                    message,
                    re.IGNORECASE,
                )
                content = (
                    content_match.group(1)
                    if content_match
                    else "Default content from pattern match"
                )
                commands.append({"action": "write", "path": path, "content": content})

            # Extract list commands
            for match in re.finditer(list_pattern, message, re.IGNORECASE):
                path = match.group(1)
                commands.append({"action": "list", "path": path})

            # Extract search commands
            for match in re.finditer(search_pattern, message, re.IGNORECASE):
                pattern = match.group(1)
                path = match.group(2)
                commands.append({"action": "search", "path": path, "pattern": pattern})

            # Extract grep commands
            for match in re.finditer(grep_pattern, message, re.IGNORECASE):
                pattern = match.group(1)
                path = match.group(2)
                commands.append({"action": "grep", "path": path, "pattern": pattern})

            # Extract cd commands
            for match in re.finditer(cd_pattern, message, re.IGNORECASE):
                path = match.group(1)
                commands.append({"action": "cd", "path": path})

            # Extract pwd commands
            if re.search(pwd_pattern, message, re.IGNORECASE):
                commands.append({"action": "pwd"})

            # Extract mkdir commands
            for match in re.finditer(mkdir_pattern, message, re.IGNORECASE):
                path = match.group(1)
                commands.append({"action": "mkdir", "path": path})

        return commands

    def _execute_file_commands(
        self, commands: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute file operation commands using MCP Filesystem Server"""
        results = []

        for cmd in commands:
            action = cmd.get("action")
            path = cmd.get("path", "")
            self.debug_print(f"Executing command: {action} {path}")

            try:
                if action == "read":
                    result = self.fs_client.read_file(path)
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "read",
                                "path": path,
                                "success": True,
                                "content": result.get("content"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "read",
                                "path": path,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "list":
                    result = self.fs_client.list_directory(path)
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "list",
                                "path": path,
                                "success": True,
                                "entries": result.get("entries"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "list",
                                "path": path,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "search":
                    pattern = cmd.get("pattern")
                    result = self.fs_client.search_files(path, pattern)
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "search",
                                "path": path,
                                "pattern": pattern,
                                "success": True,
                                "matches": result.get("matches"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "search",
                                "path": path,
                                "pattern": pattern,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "write":
                    content = cmd.get(
                        "content", "Default content from Offline File Agent"
                    )
                    result = self.fs_client.write_file(path, content)
                    results.append(
                        {
                            "action": "write",
                            "path": path,
                            "success": result.get("success", False),
                            "error": result.get("error", ""),
                        }
                    )

                elif action == "pwd" or action == "get_working_directory":
                    result = self.fs_client.get_working_directory()
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "pwd",
                                "success": True,
                                "current_dir": result.get("current_dir"),
                                "script_dir": result.get("script_dir"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "pwd",
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "cd" or action == "change_directory":
                    result = self.fs_client.change_directory(path)
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "cd",
                                "path": path,
                                "success": True,
                                "current_dir": result.get("current_dir"),
                                "previous_dir": result.get("previous_dir"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "cd",
                                "path": path,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "grep":
                    pattern = cmd.get("pattern")
                    recursive = cmd.get("recursive", True)
                    case_sensitive = cmd.get("case_sensitive", False)
                    result = self.fs_client.grep_search(
                        path, pattern, recursive, case_sensitive
                    )
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "grep",
                                "path": path,
                                "pattern": pattern,
                                "success": True,
                                "matches": result.get("matches"),
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "grep",
                                "path": path,
                                "pattern": pattern,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

                elif action == "mkdir" or action == "create_directory":
                    result = self.fs_client.create_directory(path)
                    if result.get("success", False):
                        results.append(
                            {
                                "action": "mkdir",
                                "path": path,
                                "success": True,
                            }
                        )
                    else:
                        results.append(
                            {
                                "action": "mkdir",
                                "path": path,
                                "success": False,
                                "error": result.get("error", "Unknown error"),
                            }
                        )

            except Exception as e:
                self.debug_print(f"Error executing command: {str(e)}", highlight=True)
                results.append(
                    {"action": action, "path": path, "success": False, "error": str(e)}
                )

        return results

    def format_command_results(self, results: List[Dict[str, Any]]) -> str:
        """Format command execution results for display."""
        formatted_output = ""

        for result in results:
            action = result.get("action")
            path = result.get("path", "")
            success = result.get("success", False)

            # Skip failed operations
            if not success:
                error_msg = f"\n[Failed to {action}{' ' + path if path else ''}: {result.get('error', 'Unknown error')}]\n"
                formatted_output += error_msg
                continue

            if action == "read":
                content = result.get("content", "")
                formatted_output += f"\n--- Content of {path} ---\n{content}\n---\n"

            elif action == "list":
                entries = result.get("entries", [])
                entries_text = "\n".join(
                    [
                        f"- {entry['name']}"
                        + (
                            f" [dir]"
                            if entry["type"] == "directory"
                            else f" [{entry['size']} bytes]"
                        )
                        for entry in entries
                    ]
                )
                formatted_output += (
                    f"\n--- Contents of directory {path} ---\n{entries_text}\n---\n"
                )

            elif action == "search":
                pattern = result.get("pattern", "")
                matches = result.get("matches", [])
                matches_text = "\n".join([f"- {match}" for match in matches])
                formatted_output += f"\n--- Search results for '{pattern}' in {path} ---\n{matches_text}\n---\n"

            elif action == "write":
                formatted_output += f"\n[Successfully wrote to file {path}]\n"

            elif action == "pwd":
                current_dir = result.get("current_dir", "")
                script_dir = result.get("script_dir", "")
                formatted_output += (
                    f"\n--- Current working directory ---\n{current_dir}\n"
                    f"--- Script directory ---\n{script_dir}\n---\n"
                )

            elif action == "cd":
                current_dir = result.get("current_dir", "")
                previous_dir = result.get("previous_dir", "")
                formatted_output += f"\n--- Directory changed ---\nFrom: {previous_dir}\nTo: {current_dir}\n---\n"

            elif action == "grep":
                pattern = result.get("pattern", "")
                matches = result.get("matches", [])
                if matches:
                    matches_text = "\n".join(
                        [
                            f"- {match['file']}:{match['line']}: {match['content']}"
                            for match in matches
                        ]
                    )
                    formatted_output += f"\n--- Grep results for '{pattern}' in {path} ---\n{matches_text}\n---\n"
                else:
                    formatted_output += (
                        f"\n--- No grep matches for '{pattern}' in {path} ---\n---\n"
                    )

            elif action == "mkdir":
                formatted_output += f"\n[Successfully created directory {path}]\n"

        return formatted_output

    def process_command(self, message: str) -> None:
        """Process a command from the user without LLM integration"""
        print(f"\nProcessing: {message}")

        # Process file commands in the message
        file_commands = self._extract_file_commands(message)

        if not file_commands:
            print("\nNo file commands detected. Try one of these formats:")
            print("\nXML Format (recommended):")
            print('  <mcp:filesystem><read path="/path/to/file" /></mcp:filesystem>')
            print(
                '  <mcp:filesystem><list path="/path/to/directory" /></mcp:filesystem>'
            )
            print(
                '  <mcp:filesystem><search path="/path/to/search" pattern="*.py" /></mcp:filesystem>'
            )
            print(
                '  <mcp:filesystem><write path="/path/to/file">Content goes here</write></mcp:filesystem>'
            )
            print('  <mcp:filesystem><cd path="/path/to/directory" /></mcp:filesystem>')
            print("  <mcp:filesystem><get_working_directory /></mcp:filesystem>")
            print(
                '  <mcp:filesystem><grep path="/path/to/search" pattern="search text" /></mcp:filesystem>'
            )
            print(
                '  <mcp:filesystem><create_directory path="/path/to/new/dir" /></mcp:filesystem>'
            )

            print("\nText Format (legacy):")
            print("  read file /path/to/file")
            print("  list directory /path/to/dir")
            print("  search for '*.py' in /path/to/dir")
            print("  write to file /path/to/file with content")
            print("  change directory /path/to/dir")
            print("  print working directory")
            print("  grep for 'pattern' in /path/to/dir")
            print("  create directory /path/to/dir")
            return

        file_results = self._execute_file_commands(file_commands)
        self.tool_usage.extend(file_results)

        # Format and display results
        formatted_results = self.format_command_results(file_results)
        print(formatted_results)


# Example usage for offline testing
if __name__ == "__main__":
    # Create an instance of OfflineFileAgent
    file_agent = OfflineFileAgent(mcp_fs_url="http://127.0.0.1:8000")

    # Interactive loop
    print("Offline File Agent initialized. Type 'exit' to quit.")
    print("Available command formats:")
    print("\nXML Format (recommended):")
    print('  <mcp:filesystem><read path="/path/to/file" /></mcp:filesystem>')
    print('  <mcp:filesystem><list path="/path/to/directory" /></mcp:filesystem>')
    print(
        '  <mcp:filesystem><search path="/path/to/search" pattern="*.py" /></mcp:filesystem>'
    )
    print(
        '  <mcp:filesystem><write path="/path/to/file">Content goes here</write></mcp:filesystem>'
    )
    print('  <mcp:filesystem><cd path="/path/to/directory" /></mcp:filesystem>')
    print("  <mcp:filesystem><get_working_directory /></mcp:filesystem>")
    print(
        '  <mcp:filesystem><grep path="/path/to/search" pattern="search text" /></mcp:filesystem>'
    )
    print(
        '  <mcp:filesystem><create_directory path="/path/to/new/dir" /></mcp:filesystem>'
    )

    print("\nText Format (legacy):")
    print("  read file /path/to/file")
    print("  list directory /path/to/dir")
    print("  search for '*.py' in /path/to/dir")
    print("  write to file /path/to/file with content")
    print("  change directory /path/to/dir")
    print("  print working directory")
    print("  grep for 'pattern' in /path/to/dir")
    print("  create directory /path/to/dir")

    while True:
        user_input = input("\nCommand: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        file_agent.process_command(user_input)
