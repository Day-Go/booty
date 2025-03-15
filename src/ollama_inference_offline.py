import requests
import json
import os
import re
from typing import Dict, List, Any, Optional, Union

from terminal_utils import Colors


class MCPFilesystemClient:
    """Client for interacting with the MCP Filesystem Server.

    Provides methods to perform filesystem operations through the MCP server,
    including reading and writing files, listing directories, searching files,
    and navigating the filesystem.
    """

    def __init__(self, base_url="http://127.0.0.1:8000"):
        """Initialize the MCP Filesystem Client.

        Args:
            base_url: Base URL of the MCP Filesystem Server
        """
        self.base_url = base_url

    def _print_mcp_call(self, function_name: str, params: Dict[str, Any]) -> None:
        """Print formatted MCP call information to console"""
        header = f"{Colors.BG_BLUE}{Colors.BOLD}MCP CALL{Colors.ENDC}"
        function = f"{Colors.CYAN}{Colors.BOLD}{function_name}{Colors.ENDC}"
        params_str = f"{Colors.GREEN}{json.dumps(params, indent=2)}{Colors.ENDC}"

        print(f"\n{header} {function}")
        print(f"Parameters: {params_str}")
        print(f"{Colors.BG_BLUE}{'-' * 50}{Colors.ENDC}")

    def _print_mcp_response(self, function_name: str, response: Dict[str, Any]) -> None:
        """Print formatted MCP response information to console"""
        header = f"{Colors.BG_GREEN}{Colors.BOLD}MCP RESPONSE{Colors.ENDC}"
        function = f"{Colors.CYAN}{Colors.BOLD}{function_name}{Colors.ENDC}"

        print(f"\n{header} {function}")

        # Special handling for different response types
        if "content" in response and len(response["content"]) > 500:
            # For file content responses, format specially
            content_preview = response["content"][:500]
            content_formatted = f"{Colors.GREEN}{content_preview}...{Colors.ENDC}"
            response_copy = response.copy()
            response_copy["content"] = (
                f"[First 500 chars of {len(response['content'])} total]"
            )
            response_str = (
                f"{Colors.GREEN}{json.dumps(response_copy, indent=2)}{Colors.ENDC}"
            )

            print(f"Response: {response_str}")
            print(f"\n{Colors.BG_CYAN}{Colors.BOLD}Content Preview:{Colors.ENDC}")
            print(content_formatted)
        else:
            response_str = (
                f"{Colors.GREEN}{json.dumps(response, indent=2)}{Colors.ENDC}"
            )
            print(f"Response: {response_str}")

        print(f"{Colors.BG_GREEN}{'-' * 50}{Colors.ENDC}")

    def _handle_request_error(
        self, error: requests.exceptions.RequestException, action: str
    ) -> Dict[str, Any]:
        """Handle request errors with detailed messages"""
        if isinstance(error, requests.exceptions.HTTPError):
            try:
                error_detail = error.response.json().get("detail", "Unknown error")
                error_message = f"{action} failed: {error_detail}"
            except (ValueError, KeyError):
                status_code = error.response.status_code
                error_message = (
                    f"{action} failed with status code {status_code}: {str(error)}"
                )
        elif isinstance(error, requests.exceptions.ConnectionError):
            error_message = (
                f"Connection error while {action.lower()}: MCP server may be offline"
            )
        elif isinstance(error, requests.exceptions.Timeout):
            error_message = (
                f"Timeout while {action.lower()}: The server took too long to respond"
            )
        else:
            error_message = f"Error while {action.lower()}: {str(error)}"

        error_response = {"success": False, "error": error_message}

        # Print the error response
        self._print_mcp_response(f"{action} (ERROR)", error_response)

        return error_response

    def read_file(self, path: str) -> Dict[str, Union[str, bool]]:
        """Read a file from the filesystem.

        Args:
            path: Absolute path to the file to read

        Returns:
            Dict containing file content or error information
        """
        endpoint = f"{self.base_url}/read_file"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("read_file", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("read_file", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Read file")

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file.

        Args:
            path: Absolute path to the file to write
            content: Content to write to the file

        Returns:
            Dict containing success status or error information
        """
        endpoint = f"{self.base_url}/write_file"
        payload = {"path": path, "content": content}

        # Log the MCP call
        self._print_mcp_call("write_file", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            # Log the response
            self._print_mcp_response("write_file", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Write file")

    def list_directory(self, path: str) -> Dict[str, Any]:
        """List contents of a directory.

        Args:
            path: Absolute path to the directory to list

        Returns:
            Dict containing directory entries or error information
        """
        endpoint = f"{self.base_url}/list_directory"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("list_directory", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("list_directory", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "List directory")

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory.

        Args:
            path: Absolute path to the directory to create

        Returns:
            Dict containing success status or error information
        """
        endpoint = f"{self.base_url}/create_directory"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("create_directory", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            # Log the response
            self._print_mcp_response("create_directory", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Create directory")

    def change_directory(self, path: str) -> Dict[str, Any]:
        """Change the current working directory.

        Args:
            path: Absolute path to the directory to change to

        Returns:
            Dict containing success status, current and previous directory, or error information
        """
        endpoint = f"{self.base_url}/change_directory"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("change_directory", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()

            # Log the response
            self._print_mcp_response("change_directory", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Change directory")

    def search_files(self, path: str, pattern: str) -> Dict[str, Any]:
        """Search for files matching pattern.

        Args:
            path: Base path to search in
            pattern: Glob pattern to match files

        Returns:
            Dict containing matching file paths or error information
        """
        endpoint = f"{self.base_url}/search_files"
        payload = {"path": path, "pattern": pattern}

        # Log the MCP call
        self._print_mcp_call("search_files", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("search_files", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Search files")

    def get_allowed_directories(self) -> Dict[str, Any]:
        """Get list of allowed directories.

        Returns:
            Dict containing allowed directories or error information
        """
        endpoint = f"{self.base_url}/list_allowed_directories"

        # Log the MCP call
        self._print_mcp_call("list_allowed_directories", {})

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("list_allowed_directories", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "List allowed directories")

    def get_working_directory(self) -> Dict[str, Any]:
        """Get current working directory and script directory.

        Returns:
            Dict containing current working directory and script directory
            or error information
        """
        endpoint = f"{self.base_url}/get_working_directory"

        # Log the MCP call
        self._print_mcp_call("get_working_directory", {})

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("get_working_directory", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Get working directory")

    def grep_search(
        self,
        path: str,
        pattern: str,
        recursive: bool = True,
        case_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """Search files using grep for content matching.

        Args:
            path: Base path to search in
            pattern: Grep pattern to search for
            recursive: Whether to search recursively (default: True)
            case_sensitive: Whether to use case-sensitive matching (default: False)

        Returns:
            Dict containing matching files with line content or error information
        """
        endpoint = f"{self.base_url}/grep_search"
        payload = {
            "path": path,
            "pattern": pattern,
            "recursive": recursive,
            "case_sensitive": case_sensitive,
        }

        # Log the MCP call
        self._print_mcp_call("grep_search", payload)

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            # Add success flag
            result["success"] = True

            # Log the response
            self._print_mcp_response("grep_search", result)

            return result
        except requests.exceptions.RequestException as e:
            return self._handle_request_error(e, "Grep search")


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
