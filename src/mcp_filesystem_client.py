"""Client for interacting with the MCP Filesystem Server."""

import requests
import json
from typing import Dict, List, Any, Optional, Union

try:
    from terminal_utils import Colors
except ImportError:
    from src.terminal_utils import Colors


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

