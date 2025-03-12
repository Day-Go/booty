import requests
import json
import os
import re
import time
from typing import Dict, List, Any, Optional, Union, Tuple


# ANSI color codes for terminal output formatting
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


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


class OllamaAgent:
    def __init__(
        self,
        model="qwq:latest",
        api_base="http://localhost:11434",
        mcp_fs_url="http://127.0.0.1:8000",
        max_context_tokens=32000,  # QwQ model has 32k context window
        system_prompt=None,
    ):
        self.model = model
        self.api_base = api_base
        self.conversation_history = []
        # Initialize MCP filesystem client
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        # Track tool usage
        self.tool_usage = []

        # Context management
        self.max_context_tokens = max_context_tokens
        self.system_prompt = system_prompt
        self.token_estimate_ratio = (
            4  # Approximation: 1 token ≈ 4 characters for English text
        )

    def _extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message"""
        # print(
        #    f"\n{Colors.BG_MAGENTA}{Colors.BOLD}DEBUG: Analyzing message for file commands:{Colors.ENDC}"
        # )
        # print(f"{Colors.MAGENTA}Message: {message}{Colors.ENDC}")

        # Remove thinking blocks to avoid processing commands in thinking
        cleaned_message = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL)
        print(
            f"{Colors.MAGENTA}Cleaned message (thinking blocks removed):{Colors.ENDC}"
        )
        print(f"{Colors.MAGENTA}{cleaned_message}{Colors.ENDC}")

        commands = []

        # Strict patterns for MCP file operations - each pattern must match exactly the command format
        # Using ^ and \b (word boundaries) to ensure we only match commands at the beginning of a line
        # and not partial matches within other text
        read_patterns = [
            r"(?:^|\n)\s*read\s+file\s+(/[^\s\n]+)",  # strict: read file /path/to/file
        ]

        write_patterns = [
            r"(?:^|\n)\s*write\s+to\s+file\s+(/[^\s\n]+)\s+with\s+content",  # strict: write to file /path/to/file with content
        ]

        list_patterns = [
            r"(?:^|\n)\s*list\s+directory\s+(/[^\s\n]+)",  # strict: list directory /path/to/dir
        ]

        search_patterns = [
            r"(?:^|\n)\s*search\s+for\s+\"([^\"]+)\"\s+in\s+(/[^\s\n]+)",  # strict: search for "pattern" in /path/to/dir
        ]

        pwd_patterns = [
            r"(?:^|\n)\s*pwd",  # strict: pwd
        ]

        grep_patterns = [
            r"(?:^|\n)\s*grep\s+for\s+\"([^\"]+)\"\s+in\s+(/[^\s\n]+)",  # strict: grep for "pattern" in /path/to/dir
        ]

        print(f"{Colors.MAGENTA}Looking for enhanced patterns:{Colors.ENDC}")

        # Process read patterns
        for pattern_idx, pattern in enumerate(read_patterns):
            print(
                f"{Colors.MAGENTA}- Read pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            read_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(read_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(read_matches):
                path = match.group(1).strip()
                print(
                    f"{Colors.MAGENTA}  Read match #{i + 1}: path = {path}{Colors.ENDC}"
                )
                commands.append({"action": "read", "path": path})

        # Process write patterns
        for pattern_idx, pattern in enumerate(write_patterns):
            print(
                f"{Colors.MAGENTA}- Write pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            write_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(write_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(write_matches):
                path = match.group(1).strip()
                print(
                    f"{Colors.MAGENTA}  Write match #{i + 1}: path = {path}{Colors.ENDC}"
                )
                commands.append({"action": "write", "path": path})

        # Process list patterns
        for pattern_idx, pattern in enumerate(list_patterns):
            print(
                f"{Colors.MAGENTA}- List pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            list_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(list_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(list_matches):
                path = match.group(1).strip()
                print(
                    f"{Colors.MAGENTA}  List match #{i + 1}: path = {path}{Colors.ENDC}"
                )
                commands.append({"action": "list", "path": path})

        # Process search patterns
        for pattern_idx, pattern in enumerate(search_patterns):
            print(
                f"{Colors.MAGENTA}- Search pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            search_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(search_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(search_matches):
                pattern = match.group(1).strip()
                path = match.group(2).strip()
                print(
                    f"{Colors.MAGENTA}  Search match #{i + 1}: pattern = {pattern}, path = {path}{Colors.ENDC}"
                )
                commands.append({"action": "search", "path": path, "pattern": pattern})

        # Process pwd patterns
        for pattern_idx, pattern in enumerate(pwd_patterns):
            print(
                f"{Colors.MAGENTA}- PWD pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            pwd_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(pwd_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(pwd_matches):
                print(f"{Colors.MAGENTA}  PWD match #{i + 1}{Colors.ENDC}")
                commands.append({"action": "pwd"})

        # Process grep patterns
        for pattern_idx, pattern in enumerate(grep_patterns):
            print(
                f"{Colors.MAGENTA}- Grep pattern #{pattern_idx + 1}: {pattern}{Colors.ENDC}"
            )
            grep_matches = list(re.finditer(pattern, cleaned_message, re.IGNORECASE))
            print(f"{Colors.MAGENTA}  Found {len(grep_matches)} matches{Colors.ENDC}")

            for i, match in enumerate(grep_matches):
                grep_pattern = match.group(1).strip()
                path = match.group(2).strip()
                print(
                    f"{Colors.MAGENTA}  Grep match #{i + 1}: pattern = {grep_pattern}, path = {path}{Colors.ENDC}"
                )
                commands.append(
                    {"action": "grep", "path": path, "pattern": grep_pattern}
                )

        # Special case for direct file requests like "Read CLAUDE.md" or "Read the contents of CLAUDE.md"
        if not commands:  # Only if no other commands were found
            # Check if the message is in the format "Read the contents of X"
            content_request = re.search(
                r'(?:read|show|display|get)\s+(?:the\s+)?(?:contents\s+of|file)?\s+["\']?([^"\'<>:;,\s]+\.[^"\'<>:;,\s]+)["\']?',
                cleaned_message,
                re.IGNORECASE,
            )

            if content_request:
                potential_file = content_request.group(1).strip()
                print(
                    f"{Colors.MAGENTA}Potential direct file reference: {potential_file}{Colors.ENDC}"
                )

                # Check if it looks like a file (has extension)
                if "." in potential_file:
                    print(
                        f"{Colors.MAGENTA}Adding direct file reference as read command{Colors.ENDC}"
                    )
                    commands.append({"action": "read", "path": potential_file})

        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}DEBUG: Found {len(commands)} total commands:{Colors.ENDC}"
        )
        for i, cmd in enumerate(commands):
            print(f"{Colors.MAGENTA}  Command #{i + 1}: {cmd}{Colors.ENDC}")

        return commands

    def _execute_file_commands(
        self, commands: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute file operation commands using MCP Filesystem Server"""
        results = []

        for cmd in commands:
            action = cmd.get("action")
            path = cmd.get("path")

            try:
                if action == "read":
                    result = self.fs_client.read_file(path)
                    results.append(
                        {
                            "action": "read",
                            "path": path,
                            "success": True,
                            "content": result.get("content"),
                        }
                    )

                elif action == "list":
                    result = self.fs_client.list_directory(path)
                    results.append(
                        {
                            "action": "list",
                            "path": path,
                            "success": True,
                            "entries": result.get("entries"),
                        }
                    )

                elif action == "search":
                    pattern = cmd.get("pattern")
                    result = self.fs_client.search_files(path, pattern)
                    results.append(
                        {
                            "action": "search",
                            "path": path,
                            "pattern": pattern,
                            "success": True,
                            "matches": result.get("matches"),
                        }
                    )

                elif action == "write":
                    # Simplified, would normally get content from message
                    content = "This is test content written by Ollama"
                    result = self.fs_client.write_file(path, content)
                    results.append(
                        {
                            "action": "write",
                            "path": path,
                            "success": result.get("success", False),
                        }
                    )

                elif action == "pwd":
                    result = self.fs_client.get_current_directory()
                    results.append(
                        {
                            "action": "pwd",
                            "success": True,
                            "current_dir": result.get("current_dir"),
                        }
                    )

                elif action == "grep":
                    pattern = cmd.get("pattern")
                    result = self.fs_client.grep_search(path, pattern)
                    results.append(
                        {
                            "action": "grep",
                            "path": path,
                            "pattern": pattern,
                            "success": True,
                            "matches": result.get("matches"),
                        }
                    )
            except Exception as e:
                results.append(
                    {"action": action, "path": path, "success": False, "error": str(e)}
                )

        return results

    def _generate_raw_response(self, prompt, system_prompt=None, stream=True) -> str:
        """Generate a raw response from Ollama API without any processing
        This method is used internally to get the unprocessed response from the LLM.

        If stream=True, it will stream the response to the console in real-time
        and return the complete response when done.
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Getting raw response from Ollama{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")

        endpoint = f"{self.api_base}/api/generate"

        # Build the request payload
        payload = {"model": self.model, "prompt": prompt, "stream": stream}

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make the request to Ollama API
        print(f"{Colors.YELLOW}Making request to Ollama API...{Colors.ENDC}")

        if stream:
            # Streaming implementation for better UX
            print(f"{Colors.YELLOW}Streaming raw response from Ollama...{Colors.ENDC}")
            response = requests.post(endpoint, json=payload, stream=True)

            # Check if request was successful
            response.raise_for_status()

            full_response = ""
            print("Response: ", end="", flush=True)

            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    response_part = json_response.get("response", "")
                    print(response_part, end="", flush=True)
                    full_response += response_part

                    # Check if done
                    if json_response.get("done", False):
                        print()  # Add newline at the end
                        break

            print(
                f"{Colors.YELLOW}Raw response complete ({len(full_response)} characters){Colors.ENDC}"
            )
            return full_response
        else:
            # Non-streaming implementation (for internal use)
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json().get("response", "")

            print(
                f"{Colors.YELLOW}Raw response length: {len(result)} characters{Colors.ENDC}"
            )
            return result

    def generate(self, prompt, system_prompt=None, stream=True):
        """Generate a response using Ollama API with file command detection on the response

        This is the core method that:
        1. Gets a raw response from the LLM (streaming it to the user)
        2. Extracts and executes file commands from that response
        3. Gets a continuation from the LLM with the added context
        4. Recursively processes the continuation for additional MCP commands
        5. Returns the full response with all file command results and continuations
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Starting generate with prompt:{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")
        print(f"{Colors.YELLOW}First 100 chars: {prompt[:100]}...{Colors.ENDC}")

        # Get raw response from the LLM - WITH streaming for immediate feedback
        raw_response = self._generate_raw_response(prompt, system_prompt, stream)

        # Set up to track all parts of the conversation
        full_response_parts = [raw_response]
        current_response = raw_response
        iteration_count = 0
        max_iterations = 5  # Safety limit to prevent infinite loops

        # Process commands recursively until no more are found
        while iteration_count < max_iterations:
            iteration_count += 1

            # Extract file commands from the current response segment
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Extracting file commands from response (iteration {iteration_count}){Colors.ENDC}"
            )
            file_commands = self._extract_file_commands(current_response)

            # If no more commands found, we're done
            if not file_commands:
                print(
                    f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: No more file commands found after {iteration_count} iterations{Colors.ENDC}"
                )
                break

            # Execute the file commands
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Executing {len(file_commands)} file commands from iteration {iteration_count}{Colors.ENDC}"
            )
            file_results = self._execute_file_commands(file_commands)
            self.tool_usage.extend(file_results)

            # Format the results for user display
            result_output = ""
            for result in file_results:
                action = result.get("action")
                path = result.get("path", "")  # Handle pwd which doesn't have path
                success = result.get("success", False)

                # Skip failed operations
                if not success:
                    error_msg = f"\n[Failed to {action}{' ' + path if path else ''}: {result.get('error', 'Unknown error')}]\n"
                    result_output += error_msg
                    continue

                if action == "read":
                    content = result.get("content", "")
                    result_output += f"\n--- Content of {path} ---\n{content}\n---\n"

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
                    result_output += (
                        f"\n--- Contents of directory {path} ---\n{entries_text}\n---\n"
                    )

                elif action == "search":
                    pattern = result.get("pattern", "")
                    matches = result.get("matches", [])
                    matches_text = "\n".join([f"- {match}" for match in matches])
                    result_output += f"\n--- Search results for '{pattern}' in {path} ---\n{matches_text}\n---\n"

                elif action == "write":
                    result_output += f"\n[Successfully wrote to file {path}]\n"

                elif action == "pwd":
                    current_dir = result.get("current_dir", "")
                    result_output += (
                        f"\n--- Current working directory ---\n{current_dir}\n---\n"
                    )

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
                        result_output += f"\n--- Grep results for '{pattern}' in {path} ---\n{matches_text}\n---\n"
                    else:
                        result_output += f"\n--- No grep matches for '{pattern}' in {path} ---\n---\n"

            # Add this batch of results to the conversation
            full_response_parts.append(result_output)

            # Print the file results
            if result_output:
                print(f"\n\nFile operation results (iteration {iteration_count}):")
                print(result_output)

            # Build comprehensive context with all previous responses and results
            context_so_far = "\n\n".join(full_response_parts)

            # Generate a continuation with the context from file operations
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Generating continuation with file operation results (iteration {iteration_count}){Colors.ENDC}"
            )

            # Create recursive continuation prompt that includes:
            # 1. Original prompt
            # 2. All previous responses and file operation results
            # 3. Request to continue the analysis with potential for more file operations
            continuation_prompt = f"""{prompt}

AI: {context_so_far}

[System Message]
Now that you have the file information you requested, please continue your analysis and complete your response. 
Incorporate the file information provided above. Don't repeat what you've already said, just continue where you left off.
You can use more file commands if needed for additional information.
"""

            # Get continuation from the model and stream it to the user in real-time
            print(
                f"{Colors.YELLOW}Getting continuation from model (iteration {iteration_count})...{Colors.ENDC}"
            )
            print(f"\nContinuation (iteration {iteration_count}):")

            # Use streaming for the continuation to provide real-time feedback
            continuation = self._generate_raw_response(
                continuation_prompt, system_prompt, stream=True
            )

            # Update for the next iteration
            current_response = continuation
            full_response_parts.append(continuation)

        # Join all parts to create the complete response
        full_response = "\n\n".join(full_response_parts)

        # Log completion
        if iteration_count >= max_iterations:
            warning = f"\n\n[WARNING: Reached maximum iteration limit ({max_iterations}). Some file commands might not have been processed.]"
            full_response += warning
            print(f"{Colors.BG_RED}{Colors.BOLD}{warning}{Colors.ENDC}")

        print(
            f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Completed full response after {iteration_count} iterations ({len(full_response)} chars){Colors.ENDC}"
        )
        return full_response

    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string

        This is a simple approximation - more accurate token counting
        would require a tokenizer specific to the model being used.
        """
        return len(text) // self.token_estimate_ratio

    def _check_context_size(self, history: List[Dict[str, str]]) -> Tuple[bool, int]:
        """Check if the current context size is approaching the token limit

        Args:
            history: The conversation history to check

        Returns:
            Tuple of (is_near_limit, estimated_tokens)
        """
        # Estimate token count for the entire history
        total_chars = sum(len(msg["content"]) for msg in history)
        estimated_tokens = total_chars // self.token_estimate_ratio

        # Also account for system prompt if present
        if self.system_prompt:
            system_tokens = len(self.system_prompt) // self.token_estimate_ratio
            estimated_tokens += system_tokens

        # Check if approaching limit (90% of max context)
        is_near_limit = estimated_tokens > (self.max_context_tokens * 0.9)

        print(
            f"{Colors.CYAN}Estimated context size: {estimated_tokens} tokens "
            f"(limit: {self.max_context_tokens}){Colors.ENDC}"
        )

        if is_near_limit:
            print(
                f"{Colors.BG_RED}{Colors.BOLD}WARNING: Context size is approaching the limit!{Colors.ENDC}"
            )

        return is_near_limit, estimated_tokens

    def _format_with_system_prompt(self, messages: str) -> str:
        """Format messages with system prompt at the beginning

        This ensures the system prompt is always at the start of the context,
        regardless of conversation length.
        """
        if self.system_prompt:
            return f"system: {self.system_prompt}\n\n{messages}"
        return messages

    def prune_history(self, keep_last: int = 5) -> int:
        """Prune conversation history to keep only the most recent exchanges

        Args:
            keep_last: Number of most recent exchanges to keep

        Returns:
            Number of messages removed
        """
        # Each exchange is one user message and one assistant response
        keep_msgs = min(keep_last * 2, len(self.conversation_history))

        if keep_msgs < len(self.conversation_history):
            removed_count = len(self.conversation_history) - keep_msgs
            self.conversation_history = self.conversation_history[-keep_msgs:]
            return removed_count

        return 0

    def clear_history(self) -> int:
        """Clear all conversation history

        Returns:
            Number of messages cleared
        """
        count = len(self.conversation_history)
        self.conversation_history = []
        return count

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the conversation context

        Returns:
            Dictionary with context stats
        """
        # Format history into a string to estimate token count
        if not self.conversation_history:
            estimated_tokens = 0
            if self.system_prompt:
                estimated_tokens = len(self.system_prompt) // self.token_estimate_ratio
        else:
            _, estimated_tokens = self._check_context_size(self.conversation_history)

        return {
            "messages": len(self.conversation_history),
            "exchanges": len(self.conversation_history) // 2,
            "estimated_tokens": estimated_tokens,
            "max_tokens": self.max_context_tokens,
            "usage_percentage": estimated_tokens / self.max_context_tokens * 100,
        }

    def chat(self, message, system_prompt=None, stream=True):
        """Chat interface that maintains conversation history

        This method:
        1. Records the user message in conversation history
        2. Formats the entire conversation history for the LLM
        3. Generates a response that can include file commands
        4. Processes those file commands and gets a continuation
        5. Returns a full response with file operation results and continuation

        Special commands:
        - /status: Show current context status
        - /prune [n]: Prune history to last n exchanges (default: 5)
        - /clear: Clear all conversation history
        """
        # Handle system prompt updates
        if system_prompt:
            self.system_prompt = system_prompt

        print(
            f"\n{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Starting chat with message:{Colors.ENDC}"
        )
        print(f"{Colors.CYAN}Message: {message}{Colors.ENDC}")

        # Handle special commands for context management
        if message.lower().startswith("/"):
            command_parts = message.lower().split()
            command = command_parts[0]

            if command == "/status":
                status = self.get_status()
                return (
                    f"Context Status:\n"
                    f"- Messages: {status['messages']} ({status['exchanges']} exchanges)\n"
                    f"- Estimated tokens: {status['estimated_tokens']:,} / {status['max_tokens']:,}\n"
                    f"- Context usage: {status['usage_percentage']:.1f}%\n\n"
                    f"Available commands:\n"
                    f"- /status - Show this status\n"
                    f"- /prune [n] - Keep only last n exchanges\n"
                    f"- /clear - Clear entire conversation history"
                )

            elif command == "/clear":
                cleared = self.clear_history()
                return f"Cleared {cleared} messages from conversation history."

            elif command == "/prune":
                # Extract number if provided
                keep = 5  # Default
                if len(command_parts) > 1 and command_parts[1].isdigit():
                    keep = int(command_parts[1])

                pruned = self.prune_history(keep)
                if pruned > 0:
                    return f"Pruned {pruned} messages from history, keeping last {keep} exchanges."
                else:
                    return f"No messages pruned. History already has {len(self.conversation_history) // 2} exchanges."

        # Append user message to history
        self.conversation_history.append({"role": "user", "content": message})

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Conversation history now has {len(self.conversation_history)} messages{Colors.ENDC}"
        )

        # Check context size before proceeding
        is_near_limit, token_count = self._check_context_size(self.conversation_history)

        # Warn user if context is getting too large
        if is_near_limit:
            warning = (
                f"\n{Colors.BG_RED}{Colors.BOLD}WARNING: Conversation context is getting large "
                f"({token_count:,} tokens, {token_count / self.max_context_tokens:.1%} of capacity). "
                f"Consider using /prune or /clear to manage context.{Colors.ENDC}\n"
            )
            print(warning)

        # Format the conversation history for Ollama
        formatted_messages = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in self.conversation_history]
        )

        # Always ensure system prompt is at the beginning
        if self.system_prompt:
            formatted_messages = self._format_with_system_prompt(formatted_messages)
            print(f"{Colors.CYAN}Added system prompt to context{Colors.ENDC}")

        print(
            f"{Colors.CYAN}Formatted message count: {len(self.conversation_history)}{Colors.ENDC}"
        )
        print(
            f"{Colors.CYAN}Formatted message length: {len(formatted_messages)} characters{Colors.ENDC}"
        )

        # Generate a response - this will now:
        # 1. Get the LLM's raw response
        # 2. Extract and execute any file commands in that response
        # 3. Generate a continuation with the file operation results
        # 4. Return the full response (initial + file results + continuation)
        print(f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Generating response{Colors.ENDC}")

        # We pass None for system_prompt since we already included it in formatted_messages
        response = self.generate(formatted_messages, None, stream)

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Appending assistant response to history ({len(response)} chars){Colors.ENDC}"
        )

        # Clean the response for history by separating any file operation results from the LLM's response
        # This prevents file operation results from being included in future prompts
        # Extract the LLM's parts (initial response and continuation) and join them
        if (
            "--- Content of " in response
            or "--- Contents of directory " in response
            or "--- Search results for " in response
        ):
            # Simple heuristic to separate LLM text from file operation results
            parts = response.split("\n\n")
            llm_parts = []
            in_file_results = False

            for part in parts:
                if (
                    part.startswith("--- Content of ")
                    or part.startswith("--- Contents of directory ")
                    or part.startswith("--- Search results for ")
                ):
                    in_file_results = True
                elif in_file_results and not (part.startswith("--- ") or part == "---"):
                    in_file_results = False
                    llm_parts.append(part)
                elif not in_file_results:
                    llm_parts.append(part)

            # Join the LLM parts for history (without the file operation results)
            cleaned_response = "\n\n".join(llm_parts)
            print(
                f"{Colors.CYAN}Cleaned response for history ({len(cleaned_response)} chars){Colors.ENDC}"
            )
        else:
            # No file operations found, use the full response
            cleaned_response = response

        # Append assistant response to history (cleaned version without file operations)
        self.conversation_history.append(
            {"role": "assistant", "content": cleaned_response}
        )

        # Check context size again after adding response
        is_near_limit, token_count = self._check_context_size(self.conversation_history)

        # If context is getting too large, append a warning to the response
        if is_near_limit:
            context_warning = (
                f"\n\n[WARNING: Conversation context is now {token_count:,} tokens "
                f"({token_count / self.max_context_tokens:.1%} of capacity). "
                f"Use /status to see details, /prune to remove older messages, "
                f"or /clear to reset the conversation.]"
            )
            response += context_warning

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Chat complete, history now has {len(self.conversation_history)} messages{Colors.ENDC}"
        )

        # Return the full response to the user (with file operations)
        return response


# Example usage for a coding agent with MCP filesystem integration
if __name__ == "__main__":
    # Define the system prompt with detailed file command instructions
    system_prompt = """You are an expert coding assistant with filesystem access capabilities.

To access files or directories, use ONLY these EXACT command formats in your response, each on its own line:
1. read file /path/to/file
2. list directory /path/to/dir
3. search for "pattern" in /path/to/search
4. write to file /path/to/file with content
5. pwd
6. grep for "pattern" in /path/to/search

CRITICAL REQUIREMENTS FOR COMMANDS:
- Commands MUST be written EXACTLY as shown above - any deviation will not be detected
- File paths MUST start with / (absolute paths only)
- Each command must be on its own line with no other text on that line
- For search commands, pattern must be in double quotes
- You CANNOT use any other variations or similar commands (no ls, cat, etc.)
- These commands will be detected, executed, and you'll receive the results
- DO NOT hallucinate or invent the output of these commands

COMMAND EXECUTION WORKFLOW:
1. You issue one or more file commands in your response
2. You MUST END YOUR RESPONSE immediately after issuing commands
3. The system will detect these commands, execute them, and return actual results
4. You will receive these results as input in your next context window
5. You can then analyze these real results and/or issue more commands

STOP AND WAIT REQUIREMENT:
- After issuing any MCP tool command(s), you MUST STOP your response IMMEDIATELY
- NEVER continue writing after issuing commands, as the commands need to execute first
- NEVER attempt to predict, simulate or hallucinate command results
- NEVER make up content that would be returned by file operations
- NEVER include fake file contents, directory listings, or search results
- The system will execute your commands and provide the actual results

ANTI-HALLUCINATION GUIDELINES:
- You have NO knowledge of file contents until you read them with commands
- You have NO knowledge of directory structures until you list them
- DO NOT continue your analysis until you receive actual results from commands
- If you feel compelled to guess what's in a file, STOP and issue a command to read it instead
- If you don't know what's in a directory, issue a list command first

RESPONSE STRUCTURE:
- Initial response: Introduce what you're doing and include ONE file command, then STOP
- After receiving results: Provide analysis and/or issue more commands, then STOP
- Always continue where you left off without repeating information
- Once file structure is known, you may issue multiple related commands in one response, then STOP

EXAMPLE OF CORRECT USAGE:
"I'll start by determining the current working directory to establish our absolute base path:
pwd"

[SYSTEM EXECUTES THE COMMAND AND RETURNS ACTUAL RESULTS TO YOU]

"Now that I know we're working in /home/user/project, I'll check the main implementation file and project structure:
read file /home/user/project/main.py
list directory /home/user/project"

[SYSTEM EXECUTES THESE COMMANDS AND RETURNS ACTUAL RESULTS TO YOU]

"Based on the code in main.py and the project structure I've just examined, I can see this is a Flask application. Let me examine the model implementation and configuration files:
read file /home/user/project/models/user.py
read file /home/user/project/config/settings.py
grep for "database" in /home/user/project"

[SYSTEM EXECUTES THESE COMMANDS AND RETURNS ACTUAL RESULTS TO YOU]

"Now I understand how the components work together. According to the files I've read, the system uses SQLAlchemy for database access with the following configuration..."
"""

    # Create an OllamaAgent with system prompt directly initialized
    coding_agent = OllamaAgent(
        model="qwq:latest",
        mcp_fs_url="http://127.0.0.1:8000",
        max_context_tokens=32000,  # QwQ model context size
        system_prompt=system_prompt,  # Initialize with system prompt
    )

    # Interactive loop
    print("Coding Agent with File System Access initialized. Type 'exit' to quit.")
    print(
        "\nIMPORTANT: File commands are detected in the AI's responses using strict patterns."
    )
    print(
        "The AI must follow these EXACT formats (one command per line, absolute paths only):"
    )
    print("  read file /path/to/file")
    print("  list directory /path/to/dir")
    print('  search for "pattern" in /path/to/dir')
    print("  write to file /path/to/file with content")
    print("  pwd")
    print('  grep for "pattern" in /path/to/dir')
    
    print("\nIMPORTANT WORKFLOW:")
    print("1. The AI will issue file commands and STOP its response")
    print("2. The system executes these commands and returns REAL results")
    print("3. The AI then continues based on the ACTUAL output")
    print("4. This prevents hallucination as the AI only works with real data")
    print("5. If the AI tries to continue writing after commands, it's a bug!")
    
    print("\nNEW FEATURES:")
    print(
        "1. Multi-step responses: The AI can now issue file commands, analyze results,"
    )
    print("   then issue more file commands in its continuations as needed")
    print(
        "2. Recursive command processing: Commands are processed in multiple iterations until"
    )
    print("   the response is complete with no more commands")
    print("3. Better command detection: Commands must be written exactly as shown")
    print("   above to be detected and executed")
    print("4. Context management: Use these commands to manage conversation context:")
    print("   - /status - Show current context size and usage")
    print("   - /prune [n] - Remove older messages, keeping last n exchanges")
    print("   - /clear - Clear all conversation history")
    print("\nExample questions you can ask:")
    print('- "Can you analyze how ollama_inference.py works?"')
    print('- "What\'s in the project structure and how does it all connect?"')
    print('- "Find all Python files related to Ollama integration"')
    print('- "Explain the file system operations in this project"')
    print()
    print("The AI will retrieve the necessary files and provide a thorough analysis.")
    print(
        "If context gets too large, the system will warn you and provide options to manage it."
    )
    print()
    print(f"{Colors.BG_RED}{Colors.BOLD}ANTI-HALLUCINATION REMINDER:{Colors.ENDC}")
    print(f"{Colors.RED}If the AI tries to continue after issuing commands or tries to")
    print(f"predict command results before they execute, please report this as a bug.{Colors.ENDC}")

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        # No need to pass system_prompt each time - it's stored in the agent
        response = coding_agent.chat(user_input, stream=True)
