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


class OllamaAgent:
    def __init__(
        self,
        model="qwq:latest",
        api_base="http://localhost:11434",
        mcp_fs_url="http://127.0.0.1:8000",
    ):
        self.model = model
        self.api_base = api_base
        self.conversation_history = []
        # Initialize MCP filesystem client
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        # Track tool usage
        self.tool_usage = []

    def _extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message"""
        print(
            f"\n{Colors.BG_MAGENTA}{Colors.BOLD}DEBUG: Analyzing message for file commands:{Colors.ENDC}"
        )
        print(f"{Colors.MAGENTA}Message: {message}{Colors.ENDC}")

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
                        
            print(f"{Colors.YELLOW}Raw response complete ({len(full_response)} characters){Colors.ENDC}")
            return full_response
        else:
            # Non-streaming implementation (for internal use)
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json().get("response", "")
            
            print(f"{Colors.YELLOW}Raw response length: {len(result)} characters{Colors.ENDC}")
            return result
        

    def generate(self, prompt, system_prompt=None, stream=True):
        """Generate a response using Ollama API with file command detection on the response
        
        This is the core method that:
        1. Gets a raw response from the LLM (streaming it to the user)
        2. Extracts and executes file commands from that response
        3. Gets a continuation from the LLM with the added context
        4. Returns the full response with file command results and continuation
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Starting generate with prompt:{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")
        print(f"{Colors.YELLOW}First 100 chars: {prompt[:100]}...{Colors.ENDC}")
        
        # Get raw response from the LLM - WITH streaming for immediate feedback
        raw_response = self._generate_raw_response(prompt, system_prompt, stream)
        
        # Extract file commands from the LLM's response (not from the user's prompt)
        print(f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Extracting file commands from LLM RESPONSE{Colors.ENDC}")
        file_commands = self._extract_file_commands(raw_response)
        
        # Execute any file commands found in the LLM's response
        file_results = []
        if file_commands:
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Executing {len(file_commands)} file commands from LLM response{Colors.ENDC}"
            )
            file_results = self._execute_file_commands(file_commands)
            self.tool_usage.extend(file_results)
            
            # Format the results for user display
            result_output = ""
            for result in file_results:
                action = result.get("action")
                path = result.get("path")
                success = result.get("success", False)
                
                # Skip failed operations
                if not success:
                    error_msg = f"\n[Failed to {action} {path}: {result.get('error', 'Unknown error')}]\n"
                    result_output += error_msg
                    continue
                    
                if action == "read":
                    content = result.get("content", "")
                    result_output += f"\n--- Content of {path} ---\n{content}\n---\n"
                        
                elif action == "list":
                    entries = result.get("entries", [])
                    entries_text = "\n".join([
                        f"- {entry['name']}" + 
                        (f" [dir]" if entry['type'] == 'directory' else f" [{entry['size']} bytes]")
                        for entry in entries
                    ])
                    result_output += f"\n--- Contents of directory {path} ---\n{entries_text}\n---\n"
                        
                elif action == "search":
                    pattern = result.get("pattern", "")
                    matches = result.get("matches", [])
                    matches_text = "\n".join([f"- {match}" for match in matches])
                    result_output += f"\n--- Search results for '{pattern}' in {path} ---\n{matches_text}\n---\n"
                
                elif action == "write":
                    result_output += f"\n[Successfully wrote to file {path}]\n"
            
            # Print the file results (raw response was already streamed)
            if result_output:
                # Print divider to separate raw response from file results
                print("\n\nFile operation results:")
                print(result_output)
                
            # Generate a continuation with the context from file operations
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Generating continuation with file operation results{Colors.ENDC}"
            )
            
            # Create continuation prompt that includes:
            # 1. Original prompt
            # 2. Initial response
            # 3. File operation results
            # 4. Request to continue the analysis
            continuation_prompt = f"""{prompt}

AI: {raw_response}

[File Operation Results]
{result_output}

[System Message]
Now that you have the file information you requested, please continue your analysis and complete your response. 
Incorporate the file information provided above. Don't repeat what you've already said, just continue where you left off.
"""
            
            # Get continuation from the model (without streaming it immediately)
            print(f"{Colors.YELLOW}Getting continuation from model with file context...{Colors.ENDC}")
            continuation = self._generate_raw_response(continuation_prompt, system_prompt, stream=False)
            
            # Print the continuation
            print("\nContinuation:")
            print(continuation)
            
            # Create the full response: initial response + file results + continuation
            full_response = raw_response + "\n\n" + result_output + "\n\n" + continuation
            
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Completed full response with continuation ({len(full_response)} chars){Colors.ENDC}"
            )
            return full_response
            
        else:
            # No file commands found, just return the raw response
            # (which was already streamed to the user)
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Completed response, no file commands ({len(raw_response)} chars){Colors.ENDC}"
            )
            return raw_response

    def chat(self, message, system_prompt=None, stream=True):
        """Chat interface that maintains conversation history
        
        This method:
        1. Records the user message in conversation history
        2. Formats the entire conversation history for the LLM
        3. Generates a response that can include file commands
        4. Processes those file commands and gets a continuation
        5. Returns a full response with file operation results and continuation
        """
        print(
            f"\n{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Starting chat with message:{Colors.ENDC}"
        )
        print(f"{Colors.CYAN}Message: {message}{Colors.ENDC}")

        # Append user message to history
        self.conversation_history.append({"role": "user", "content": message})

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Conversation history now has {len(self.conversation_history)} messages{Colors.ENDC}"
        )

        # Format the conversation history for Ollama
        formatted_messages = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in self.conversation_history
            ]
        )

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
        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Generating response{Colors.ENDC}"
        )
        response = self.generate(formatted_messages, system_prompt, stream)
        
        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Appending assistant response to history ({len(response)} chars){Colors.ENDC}"
        )
        
        # Clean the response for history by separating any file operation results from the LLM's response
        # This prevents file operation results from being included in future prompts
        # Extract the LLM's parts (initial response and continuation) and join them
        if "--- Content of " in response or "--- Contents of directory " in response or "--- Search results for " in response:
            # Simple heuristic to separate LLM text from file operation results
            parts = response.split("\n\n")
            llm_parts = []
            in_file_results = False
            
            for part in parts:
                if part.startswith("--- Content of ") or part.startswith("--- Contents of directory ") or part.startswith("--- Search results for "):
                    in_file_results = True
                elif in_file_results and not (part.startswith("--- ") or part == "---"):
                    in_file_results = False
                    llm_parts.append(part)
                elif not in_file_results:
                    llm_parts.append(part)
            
            # Join the LLM parts for history (without the file operation results)
            cleaned_response = "\n\n".join(llm_parts)
            print(f"{Colors.CYAN}Cleaned response for history ({len(cleaned_response)} chars){Colors.ENDC}")
        else:
            # No file operations found, use the full response
            cleaned_response = response
        
        # Append assistant response to history (cleaned version without file operations)
        self.conversation_history.append({"role": "assistant", "content": cleaned_response})

        print(
            f"{Colors.BG_CYAN}{Colors.BOLD}DEBUG: Chat complete, history now has {len(self.conversation_history)} messages{Colors.ENDC}"
        )
        
        # Return the full response to the user (with file operations)
        return response


# Example usage for a coding agent with MCP filesystem integration
if __name__ == "__main__":
    # Create an instance of OllamaAgent with QwQ model and MCP filesystem integration
    coding_agent = OllamaAgent(model="qwq:latest", mcp_fs_url="http://127.0.0.1:8000")

    system_prompt = """You are an expert coding assistant with filesystem access capabilities.

To access files or directories, use ONLY these EXACT command formats in your response, each on its own line:

1. read file /path/to/file
2. list directory /path/to/dir
3. search for "pattern" in /path/to/search
4. write to file /path/to/file with content

CRITICAL REQUIREMENTS FOR COMMANDS:
- Commands MUST be written EXACTLY as shown above - any deviation will not be detected
- File paths MUST start with / (absolute paths only)
- Each command must be on its own line with no other text on that line
- For search commands, pattern must be in double quotes
- You CANNOT use any other variations or similar commands (no ls, cat, etc.)
- These commands will be detected, executed, and you'll receive the results

RESPONSE STRUCTURE:
- First part: Introduce what you're doing and include exact file commands
- Second part: After receiving file data, continue your analysis with that information
- DO NOT repeat your first response in the second part - just continue the analysis

EXAMPLE OF CORRECT USAGE:

"I'll analyze this code by first checking the main implementation:
read file /home/dago/dev/projects/llm/src/ollama_inference.py

Let me also see what's in the project configuration:
list directory /home/dago/dev/projects/llm

And check for any API-related code:
search for "api" in /home/dago/dev/projects/llm/src"

[After receiving file operation results, you'll continue with:]
"Based on the code, I can see that ollama_inference.py implements a client for..."
"""

    # Interactive loop
    print("Coding Agent with File System Access initialized. Type 'exit' to quit.")
    print("\nIMPORTANT: File commands are detected in the AI's responses using strict patterns.")
    print("The AI must follow these EXACT formats (one command per line, absolute paths only):")
    print("  read file /path/to/file")
    print("  list directory /path/to/dir")
    print("  search for \"pattern\" in /path/to/dir")
    print("  write to file /path/to/file with content")
    print("\nNEW FEATURES:")
    print("1. Two-part responses: The AI will first issue file commands, then")
    print("   continue its analysis after receiving the file contents")
    print("2. Better command detection: Commands must be written exactly as shown")
    print("   above to be detected and executed")
    print("\nExample questions you can ask:")
    print("- \"Can you analyze how ollama_inference.py works?\"")
    print("- \"What's in the project structure and how does it all connect?\"")
    print("- \"Find all Python files related to Ollama integration\"")
    print("- \"Explain the file system operations in this project\"")
    print()
    print("The AI will retrieve the necessary files and provide a thorough analysis.")

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        coding_agent.chat(user_input, system_prompt=system_prompt)
