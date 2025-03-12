import requests
import json
import os
import re
import time
import xml.etree.ElementTree as ET
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


class StreamingXMLParser:
    """Streaming parser for XML-based MCP commands"""
    def __init__(self):
        # Parser state
        self.in_mcp_block = False
        self.buffer = ""
        self.xml_stack = []
        self.complete_command = ""
        self.in_think_block = False

    def feed(self, token: str) -> bool:
        """
        Process a new token and update parser state.
        
        Returns True if a complete MCP command is detected.
        """
        # Track if we're inside thinking blocks
        if "<think>" in self.buffer + token and not self.in_think_block:
            self.in_think_block = True
            
        if "</think>" in self.buffer + token and self.in_think_block:
            self.in_think_block = False
            # Clear buffer after exiting think block since we don't want to process commands in thinking
            self.buffer = ""
            return False

        # Skip processing if inside a thinking block
        if self.in_think_block:
            self.buffer += token
            return False
            
        # Add token to buffer
        self.buffer += token
        
        # Detect opening of MCP block
        if "<mcp:filesystem>" in self.buffer and not self.in_mcp_block:
            self.in_mcp_block = True
            self.xml_stack.append("mcp:filesystem")
            self.complete_command = "<mcp:filesystem>"
            # Remove everything before the opening tag
            start_idx = self.buffer.find("<mcp:filesystem>") + len("<mcp:filesystem>")
            self.buffer = self.buffer[start_idx:]
            
        # Process content inside MCP block
        if self.in_mcp_block:
            # Track XML tag openings
            for match in re.finditer(r"<(\w+)[^>]*>", self.buffer):
                tag = match.group(1)
                if not match.group(0).endswith("/>"):  # Not a self-closing tag
                    self.xml_stack.append(tag)
                    
            # Track XML tag closings
            for match in re.finditer(r"</(\w+)>", self.buffer):
                tag = match.group(1)
                if self.xml_stack and self.xml_stack[-1] == tag:
                    self.xml_stack.pop()
                    
                    # Check if we've closed the MCP block
                    if not self.xml_stack and tag == "mcp:filesystem":
                        # We have a complete command
                        end_idx = match.end()
                        self.complete_command += self.buffer[:end_idx]
                        self.buffer = self.buffer[end_idx:]
                        self.in_mcp_block = False
                        return True
                        
            # Update the complete command with the buffer and clear the buffer
            # only if we're still in an MCP block
            if self.in_mcp_block:
                self.complete_command += self.buffer
                self.buffer = ""
                
        return False

    def get_command(self) -> str:
        """Return the complete MCP command"""
        command = self.complete_command
        self.complete_command = ""
        return command
        
    def reset(self):
        """Reset parser state"""
        self.in_mcp_block = False
        self.buffer = ""
        self.xml_stack = []
        self.complete_command = ""
        self.in_think_block = False


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
        """Extract file operation commands from a message using XML format"""
        # Remove thinking blocks to avoid processing commands in thinking
        cleaned_message = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL)
        print(
            f"{Colors.MAGENTA}Cleaned message (thinking blocks removed):{Colors.ENDC}"
        )
        print(f"{Colors.MAGENTA}{cleaned_message}{Colors.ENDC}")

        commands = []
        
        # Use XML parsing for command extraction
        # Look for <mcp:filesystem> tags in the message
        try:
            # Find all <mcp:filesystem> blocks in the message
            mcp_blocks = re.findall(r'<mcp:filesystem>(.*?)</mcp:filesystem>', cleaned_message, re.DOTALL)
            
            print(f"{Colors.MAGENTA}Found {len(mcp_blocks)} MCP filesystem blocks{Colors.ENDC}")
            
            # Process each MCP block using XML parsing
            for block_idx, block in enumerate(mcp_blocks):
                print(f"{Colors.MAGENTA}Processing MCP block #{block_idx + 1}:{Colors.ENDC}")
                print(f"{Colors.MAGENTA}{block}{Colors.ENDC}")
                
                # Wrap the block in a root element for proper XML parsing
                xml_content = f"<root>{block}</root>"
                
                # Use a more permissive approach for handling potentially malformed XML
                try:
                    root = ET.fromstring(xml_content)
                    
                    # Process each command element in the block
                    for cmd_element in root:
                        cmd_type = cmd_element.tag.lower()
                        print(f"{Colors.MAGENTA}Processing command type: {cmd_type}{Colors.ENDC}")
                        
                        # Convert XML elements to command dictionaries
                        if cmd_type == "read":
                            path = cmd_element.get("path", "")
                            if path:
                                print(f"{Colors.MAGENTA}Read command with path: {path}{Colors.ENDC}")
                                commands.append({"action": "read", "path": path})
                        
                        elif cmd_type == "write":
                            path = cmd_element.get("path", "")
                            content = cmd_element.text if cmd_element.text else ""
                            if path:
                                print(f"{Colors.MAGENTA}Write command with path: {path}{Colors.ENDC}")
                                commands.append({"action": "write", "path": path, "content": content})
                        
                        elif cmd_type == "list":
                            path = cmd_element.get("path", "")
                            if path:
                                print(f"{Colors.MAGENTA}List command with path: {path}{Colors.ENDC}")
                                commands.append({"action": "list", "path": path})
                        
                        elif cmd_type == "search":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                print(f"{Colors.MAGENTA}Search command with path: {path}, pattern: {pattern}{Colors.ENDC}")
                                commands.append({"action": "search", "path": path, "pattern": pattern})
                        
                        elif cmd_type == "pwd":
                            print(f"{Colors.MAGENTA}PWD command{Colors.ENDC}")
                            commands.append({"action": "pwd"})
                        
                        elif cmd_type == "grep":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                print(f"{Colors.MAGENTA}Grep command with path: {path}, pattern: {pattern}{Colors.ENDC}")
                                commands.append({"action": "grep", "path": path, "pattern": pattern})
                                
                except Exception as xml_error:
                    print(f"{Colors.RED}Error parsing XML: {str(xml_error)}{Colors.ENDC}")
                    # Fall back to regex-based extraction for this block if XML parsing fails
                    
        except Exception as e:
            print(f"{Colors.RED}Error extracting MCP commands: {str(e)}{Colors.ENDC}")
            
        # Fallback for direct file references outside XML structure
        # Only if no commands were found using XML parsing
        if not commands:
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
                    # Extract content from command if available
                    content = cmd.get("content", "This is test content written by Ollama")
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
        
    def _format_command_results(self, results: List[Dict[str, Any]]) -> str:
        """Format command execution results for inclusion in the model context"""
        result_output = ""
        for result in results:
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
                    
        return result_output

    def _generate_raw_response(self, prompt, system_prompt=None, stream=True) -> str:
        """Generate a raw response from Ollama API with streaming command detection
        
        This method now:
        1. Streams tokens from the LLM
        2. Monitors for complete MCP filesystem XML commands
        3. Interrupts generation when a command is detected
        4. Executes the command and injects the result
        5. Continues generation with the new context
        
        If stream=True, it will stream the response to the console in real-time
        and handle MCP commands on-the-fly.
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Getting raw response from Ollama{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")

        endpoint = f"{self.api_base}/api/generate"

        # Build the request payload
        payload = {"model": self.model, "prompt": prompt, "stream": True}  # Always stream for command detection

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make the request to Ollama API
        print(f"{Colors.YELLOW}Making request to Ollama API...{Colors.ENDC}")

        # Initialize the streaming parser
        xml_parser = StreamingXMLParser()
        
        # Initialize response tracking
        full_response = ""
        should_continue = True
        has_completed = False
        
        # Track if we need to continue generation after command execution
        need_continuation = False
        
        while should_continue:
            # Make the API request
            print(f"{Colors.YELLOW}Streaming response with command detection...{Colors.ENDC}")
            response = requests.post(endpoint, json=payload, stream=True)
            response.raise_for_status()
            
            if not need_continuation:
                print("Response: ", end="", flush=True)
            
            # Process the streaming response token by token
            for line in response.iter_lines():
                if not line:
                    continue
                    
                json_response = json.loads(line)
                response_part = json_response.get("response", "")
                
                # Print token to user if we're not in continuation mode
                if stream:
                    print(response_part, end="", flush=True)
                
                # Check if the model is done generating
                if json_response.get("done", False):
                    has_completed = True
                    if stream:
                        print()  # Add newline
                    break
                
                # Add token to response
                full_response += response_part
                
                # Process token with XML parser
                if xml_parser.feed(response_part):
                    # Complete MCP command detected - interrupt generation
                    print(f"\n{Colors.BG_MAGENTA}{Colors.BOLD}MCP COMMAND DETECTED - INTERRUPTING GENERATION{Colors.ENDC}")
                    
                    # Get the complete command
                    mcp_command = xml_parser.get_command()
                    print(f"{Colors.MAGENTA}Complete command: {mcp_command}{Colors.ENDC}")
                    
                    # Extract file commands from the XML
                    commands = self._extract_file_commands(mcp_command)
                    
                    if commands:
                        # Execute the commands
                        print(f"{Colors.BG_BLUE}{Colors.BOLD}EXECUTING MCP COMMANDS{Colors.ENDC}")
                        results = self._execute_file_commands(commands)
                        
                        # Format the results for display
                        result_output = self._format_command_results(results)
                        
                        # Add results to full response
                        full_response += "\n" + result_output
                        
                        if stream:
                            print(f"\n{result_output}")
                        
                        # Set up for continuation
                        need_continuation = True
                        
                        # Update the prompt with results for continuation
                        prompt = f"{prompt}\n\nAI: {full_response}\n\n[System Message]\nNow that you have the requested information, please continue your response incorporating this information."
                        payload = {"model": self.model, "prompt": prompt, "stream": True}
                        if system_prompt:
                            payload["system"] = system_prompt
                            
                        # Reset the XML parser for the continuation
                        xml_parser.reset()
                        
                        # Break out of the token loop to start a new request
                        break
            
            # If the model finished generating and we don't need continuation, we're done
            if has_completed and not need_continuation:
                should_continue = False
            
            # If we need to continue after a command, we'll make another request
            if need_continuation:
                # Reset for next cycle
                need_continuation = False
                print(f"\n{Colors.BG_BLUE}{Colors.BOLD}CONTINUING GENERATION WITH COMMAND RESULTS{Colors.ENDC}\n")
        
        # Final response
        print(f"{Colors.YELLOW}Response complete ({len(full_response)} characters){Colors.ENDC}")
        return full_response

    def generate(self, prompt, system_prompt=None, stream=True):
        """Generate a response using Ollama API with real-time command detection
        
        This is the core method that:
        1. Gets a raw response from the LLM, watching for MCP commands in real-time
        2. When a command is detected, interrupts the generation to execute it
        3. Injects the command results and continues generation
        4. Repeats until the complete response is generated
        5. Returns the full response with all embedded command results
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Starting generate with prompt:{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")
        print(f"{Colors.YELLOW}First 100 chars: {prompt[:100]}...{Colors.ENDC}")

        # Get response with interactive command detection and execution
        response = self._generate_raw_response(prompt, system_prompt, stream)
        
        return response

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
        3. Generates a response with real-time MCP command detection and execution
        4. Returns a full response with all command results embedded
        
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

        # Generate a response with real-time command detection
        print(f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Generating response{Colors.ENDC}")

        # We pass None for system_prompt since we already included it in formatted_messages
        response = self.generate(formatted_messages, None, stream)

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Appending assistant response to history ({len(response)} chars){Colors.ENDC}"
        )

        # Clean the response for history by separating any file operation results
        # Extract all command results from the response to avoid storing them in history
        cleaned_response = response
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

To access files or directories, use XML-formatted commands within <mcp:filesystem> tags. Here's how to use them:

<mcp:filesystem>
    <read path="/path/to/file" />
    <write path="/path/to/file">Content to write to the file</write>
    <list path="/path/to/directory" />
    <search path="/path/to/search" pattern="search pattern" />
    <pwd />
    <grep path="/path/to/search" pattern="grep pattern" />
</mcp:filesystem>

CRITICAL REQUIREMENTS FOR COMMANDS:
- Commands MUST be wrapped in <mcp:filesystem> tags
- Each command is an XML element with appropriate attributes
- File paths MUST start with / (absolute paths only)
- Use proper XML syntax - each tag must be properly closed
- For write commands, place the content between opening and closing tags
- Pattern attributes must be enclosed in quotes
- These commands will be detected and executed in real-time as you generate them
- DO NOT hallucinate or invent the output of these commands

COMMAND EXECUTION WORKFLOW:
1. When you issue an MCP filesystem command, your generation will be immediately interrupted
2. The command will be executed and the results will be shown
3. You will then continue your response incorporating the command results
4. You can use multiple commands throughout your response as needed

ANTI-HALLUCINATION GUIDELINES:
- You have NO knowledge of file contents until you read them with commands
- You have NO knowledge of directory structures until you list them
- If you feel compelled to guess what's in a file, issue a command to read it instead
- If you don't know what's in a directory, issue a list command first

EXAMPLE OF CORRECT USAGE:
"I'll start by determining the current working directory to establish our absolute base path:

<mcp:filesystem>
    <pwd />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now that I know we're working in /home/user/project, I'll check the main implementation file and project structure:

<mcp:filesystem>
    <read path="/home/user/project/main.py" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"I see this is a Flask application. Let me look at the directory structure:

<mcp:filesystem>
    <list path="/home/user/project" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now I'll examine the model implementation files:

<mcp:filesystem>
    <read path="/home/user/project/models/user.py" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now I understand how the components work together. According to the files I've read, the system uses SQLAlchemy for database access..."
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
        "\nIMPORTANT: File commands are now detected and executed in real-time using XML syntax."
    )
    print(
        "The AI uses these formats within <mcp:filesystem> tags:"
    )
    print("  <read path=\"/path/to/file\" />")
    print("  <list path=\"/path/to/dir\" />")
    print("  <search path=\"/path/to/dir\" pattern=\"search pattern\" />")
    print("  <write path=\"/path/to/file\">Content goes here</write>")
    print("  <pwd />")
    print("  <grep path=\"/path/to/dir\" pattern=\"grep pattern\" />")
    
    print("\nIMPORTANT WORKFLOW:")
    print("1. When the AI uses a command, generation is immediately interrupted")
    print("2. The system executes the command and shows REAL results")
    print("3. The AI then continues its response incorporating the results")
    print("4. This prevents hallucination as the AI only works with real data")
    print("5. The AI can use multiple commands throughout its response")
    
    print("\nNEW FEATURES:")
    print(
        "1. Real-time XML command detection and execution"
    )
    print("2. Streaming token analysis for immediate command processing")
    print("3. Seamless interruption and continuation of model generation")
    print("4. Better handling of complex multi-line content")
    print("5. Context management: Use these commands to manage conversation context:")
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

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        # No need to pass system_prompt each time - it's stored in the agent
        response = coding_agent.chat(user_input, stream=True)