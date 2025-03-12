"""Client for interacting with the MCP Filesystem Server."""

import requests
import json
from typing import Dict, List, Any
from terminal_utils import Colors


class MCPFilesystemClient:
    """Client for interacting with the MCP Filesystem Server"""

    def __init__(self, base_url="http://127.0.0.1:8000"):
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

    def read_file(self, path: str) -> Dict[str, str]:
        """Read a file from the filesystem"""
        endpoint = f"{self.base_url}/read_file"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("read_file", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("read_file", result)

        return result

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        endpoint = f"{self.base_url}/write_file"
        payload = {"path": path, "content": content}

        # Log the MCP call
        self._print_mcp_call("write_file", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("write_file", result)

        return result

    def list_directory(self, path: str) -> Dict[str, Any]:
        """List contents of a directory"""
        endpoint = f"{self.base_url}/list_directory"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("list_directory", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("list_directory", result)

        return result

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        endpoint = f"{self.base_url}/create_directory"
        payload = {"path": path}

        # Log the MCP call
        self._print_mcp_call("create_directory", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("create_directory", result)

        return result

    def search_files(self, path: str, pattern: str) -> Dict[str, List[str]]:
        """Search for files matching pattern"""
        endpoint = f"{self.base_url}/search_files"
        payload = {"path": path, "pattern": pattern}

        # Log the MCP call
        self._print_mcp_call("search_files", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("search_files", result)

        return result

    def get_allowed_directories(self) -> Dict[str, List[str]]:
        """Get list of allowed directories"""
        endpoint = f"{self.base_url}/list_allowed_directories"

        # Log the MCP call
        self._print_mcp_call("list_allowed_directories", {})

        response = requests.get(endpoint)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("list_allowed_directories", result)

        return result

    def get_current_directory(self) -> Dict[str, str]:
        """Get the current working directory"""
        endpoint = f"{self.base_url}/pwd"

        # Log the MCP call
        self._print_mcp_call("pwd", {})

        response = requests.get(endpoint)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("pwd", result)

        return result

    def grep_search(
        self,
        path: str,
        pattern: str,
        recursive: bool = True,
        case_sensitive: bool = False,
    ) -> Dict[str, List[Dict[str, str]]]:
        """Search files using grep for content matching"""
        endpoint = f"{self.base_url}/grep_search"
        payload = {
            "path": path,
            "pattern": pattern,
            "recursive": recursive,
            "case_sensitive": case_sensitive,
        }

        # Log the MCP call
        self._print_mcp_call("grep_search", payload)

        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        result = response.json()

        # Log the response
        self._print_mcp_response("grep_search", result)

        return result