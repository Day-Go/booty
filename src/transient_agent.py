"""Transient Agent for handling delegated tasks with clean context."""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import requests

from terminal_utils import Colors
from mcp_filesystem_client import MCPFilesystemClient
from xml_parser import StreamingXMLParser


class TransientAgent:
    """Lightweight agent for executing specific delegated tasks."""
    
    def __init__(
        self,
        task_id: str,
        task_description: str,
        model: str = "qwq:latest",
        api_base: str = "http://localhost:11434",
        mcp_fs_url: str = "http://127.0.0.1:8000",
        system_prompt: str = None,
    ):
        """Initialize a TransientAgent instance.
        
        Args:
            task_id: Unique identifier for the task
            task_description: Description of the delegated task
            model: Ollama model to use
            api_base: Ollama API base URL
            mcp_fs_url: MCP filesystem server URL
            system_prompt: Optional system prompt to guide the agent
        """
        self.task_id = task_id
        self.task_description = task_description
        self.model = model
        self.api_base = api_base
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        self.system_prompt = system_prompt
        self.result = None
        self.status = "initialized"
        
        # Predefined system prompt if none provided
        if not self.system_prompt:
            self.system_prompt = (
                "You are a focused agent tasked with a specific job. "
                "Execute the task efficiently and return a concise summary of findings. "
                "Use available tools when needed. Do not add extraneous explanations."
            )
            
        print(
            f"{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {task_id}: Initialized for task: {task_description}{Colors.ENDC}"
        )
            
    def execute(self, context_summary: str, stream: bool = True) -> Dict[str, Any]:
        """Execute the delegated task and return results.
        
        Args:
            context_summary: Summarized context to provide task background
            stream: Whether to stream the response
            
        Returns:
            Dictionary with task results and metadata
        """
        self.status = "running"
        print(
            f"{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: Executing task{Colors.ENDC}"
        )
        
        # Create prompt with task description and context
        prompt = (
            f"# TASK ASSIGNMENT\n{self.task_description}\n\n"
            f"# CONTEXT\n{context_summary}\n\n"
            f"Execute this task and provide a concise response. "
            f"Focus on giving exactly what was requested. "
            f"If you use any tools like file operations, include key findings but "
            f"summarize verbose outputs to keep your response compact."
        )
        
        # Generate response from Ollama
        try:
            print(
                f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: Generating response for task{Colors.ENDC}"
            )
            
            # Get raw response with command execution
            response = self._generate_raw_response(prompt, self.system_prompt, stream)
            
            # Process the response to create a structured result
            result = self._process_response(response)
            
            self.result = result
            self.status = "completed"
            
            print(
                f"{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: Task completed "
                f"successfully ({len(result['summary'])} chars summary){Colors.ENDC}"
            )
            
            return result
            
        except Exception as e:
            error_message = f"TRANSIENT AGENT ERROR: {str(e)}"
            print(f"{Colors.BG_RED}{Colors.BOLD}{error_message}{Colors.ENDC}")
            
            self.result = {
                "task_id": self.task_id,
                "status": "failed",
                "error": str(e),
                "summary": f"Failed to complete task: {str(e)}",
                "raw_response": None
            }
            self.status = "failed"
            
            return self.result
    
    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process the raw response into a structured result.
        
        Args:
            response: The raw response from Ollama
            
        Returns:
            Structured result dictionary
        """
        # Extract any file operation results to store separately
        file_results = []
        
        # Look for file operation blocks with regex
        file_blocks = re.findall(
            r"---\s+(Content of|Contents of directory|Search results for|Grep results for)[^-]+---\s+(.*?)---",
            response,
            re.DOTALL
        )
        
        # Store each file operation block
        for block_type, content in file_blocks:
            file_results.append({
                "type": block_type,
                "content": content.strip()
            })
        
        # Create a clean summary by removing file operation blocks
        summary = re.sub(
            r"---\s+(Content of|Contents of directory|Search results for|Grep results for)[^-]+---\s+.*?---",
            "",
            response,
            flags=re.DOTALL
        )
        
        # Clean up any double newlines from removed blocks
        summary = re.sub(r"\n{3,}", "\n\n", summary)
        summary = summary.strip()
        
        # If summary is too long, create a more concise version
        if len(summary) > 1000:
            # Keep key findings section if it exists
            key_findings_match = re.search(r"(?:Key Findings|Summary|Results):(.*?)(?:\n\n|$)", summary, re.DOTALL | re.IGNORECASE)
            
            if key_findings_match:
                concise_summary = f"Summary: {key_findings_match.group(1).strip()}"
            else:
                # Otherwise take the first paragraph and append a note
                first_para = summary.split("\n\n")[0].strip()
                concise_summary = f"{first_para}\n\n[Full response was {len(summary)} chars and has been summarized]"
        else:
            concise_summary = summary
            
        # Structure the result
        result = {
            "task_id": self.task_id,
            "status": "completed",
            "summary": concise_summary,
            "file_operations": file_results,
            "raw_response": response
        }
        
        return result
        
    def _extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message using XML format.
        
        Args:
            message: The message to extract commands from
            
        Returns:
            List of command dictionaries
        """
        # Remove thinking blocks to avoid processing commands in thinking
        cleaned_message = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL)
        
        commands = []
        
        # Use XML parsing for command extraction
        # Look for <mcp:filesystem> tags in the message
        try:
            # Find all <mcp:filesystem> blocks in the message
            mcp_blocks = re.findall(
                r"<mcp:filesystem>(.*?)</mcp:filesystem>", cleaned_message, re.DOTALL
            )
            
            print(
                f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: Found {len(mcp_blocks)} MCP filesystem blocks{Colors.ENDC}"
            )
            
            # Process each MCP block using XML parsing
            for block_idx, block in enumerate(mcp_blocks):
                # Wrap the block in a root element for proper XML parsing
                xml_content = f"<root>{block}</root>"
                
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_content)
                    
                    # Process each command element in the block
                    for cmd_element in root:
                        cmd_type = cmd_element.tag.lower()
                        
                        # Convert XML elements to command dictionaries
                        if cmd_type == "read":
                            path = cmd_element.get("path", "")
                            if path:
                                commands.append({"action": "read", "path": path})
                                
                        elif cmd_type == "write":
                            path = cmd_element.get("path", "")
                            content = cmd_element.text if cmd_element.text else ""
                            if path:
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
                                commands.append({"action": "list", "path": path})
                                
                        elif cmd_type == "search":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                commands.append(
                                    {
                                        "action": "search",
                                        "path": path,
                                        "pattern": pattern,
                                    }
                                )
                                
                        elif cmd_type == "pwd":
                            commands.append({"action": "pwd"})
                            
                        elif cmd_type == "grep":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                commands.append(
                                    {"action": "grep", "path": path, "pattern": pattern}
                                )
                                
                except Exception as xml_error:
                    print(
                        f"{Colors.RED}TRANSIENT AGENT {self.task_id}: Error parsing XML: {str(xml_error)}{Colors.ENDC}"
                    )
                    
        except Exception as e:
            print(
                f"{Colors.RED}TRANSIENT AGENT {self.task_id}: Error extracting MCP commands: {str(e)}{Colors.ENDC}"
            )
            
        # Fallback for direct file references outside XML structure
        if not commands:
            # Check if the message is in the format "Read the contents of X"
            content_request = re.search(
                r'(?:read|show|display|get)\s+(?:the\s+)?(?:contents\s+of|file)?\s+["\']?([^"\'<>:;,\s]+\.[^"\'<>:;,\s]+)["\']?',
                cleaned_message,
                re.IGNORECASE,
            )
            
            if content_request:
                potential_file = content_request.group(1).strip()
                
                # Check if it looks like a file (has extension)
                if "." in potential_file:
                    commands.append({"action": "read", "path": potential_file})
                    
        return commands
            
    def _execute_file_commands(self, commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute file operation commands using MCP Filesystem Server.
        
        Args:
            commands: List of command dictionaries to execute
            
        Returns:
            List of result dictionaries
        """
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
        """Format command execution results for inclusion in the model context.
        
        Args:
            results: List of command result dictionaries
            
        Returns:
            Formatted result string
        """
        result_output = ""
        
        for result in results:
            action = result.get("action")
            path = result.get("path", "")
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
                result_output += f"\n--- Contents of directory {path} ---\n{entries_text}\n---\n"
                
            elif action == "search":
                pattern = result.get("pattern", "")
                matches = result.get("matches", [])
                matches_text = "\n".join([f"- {match}" for match in matches])
                result_output += f"\n--- Search results for '{pattern}' in {path} ---\n{matches_text}\n---\n"
                
            elif action == "write":
                result_output += f"\n[Successfully wrote to file {path}]\n"
                
            elif action == "pwd":
                current_dir = result.get("current_dir", "")
                result_output += f"\n--- Current working directory ---\n{current_dir}\n---\n"
                
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
        """Generate a raw response from Ollama API with command detection.
        
        Args:
            prompt: The prompt to send to Ollama
            system_prompt: Optional system prompt
            stream: Whether to stream the response
            
        Returns:
            Raw response string
        """
        print(
            f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: Getting raw response from Ollama{Colors.ENDC}"
        )
        
        endpoint = f"{self.api_base}/api/generate"
        
        # Build the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,  # Always stream for command detection
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            
        # Make the request to Ollama API
        print(
            f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: Making request to Ollama API{Colors.ENDC}"
        )
        
        # Initialize the streaming parser
        xml_parser = StreamingXMLParser(debug_mode=False)
        
        # Initialize response tracking
        full_response = ""
        accumulated_tokens = ""
        should_continue = True
        has_completed = False
        
        # Track if we need to continue generation after command execution
        need_continuation = False
        
        # Maximum size before checking accumulated tokens for fallback detection
        accumulated_tokens_max = 500
        
        while should_continue:
            # Make the API request
            response = requests.post(endpoint, json=payload, stream=True)
            response.raise_for_status()
            
            if not need_continuation and stream:
                print(f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: ", end="", flush=True)
                
            # Process the streaming response token by token
            for line in response.iter_lines():
                if not line:
                    continue
                    
                try:
                    json_response = json.loads(line)
                    response_part = json_response.get("response", "")
                    
                    # Print token to user if we're streaming
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
                    accumulated_tokens += response_part
                    
                    # Process token with XML parser
                    if xml_parser.feed(response_part):
                        # Complete MCP command detected - interrupt generation
                        print(
                            f"\n{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                            f"MCP COMMAND DETECTED - INTERRUPTING{Colors.ENDC}"
                        )
                        
                        # Get the complete command
                        mcp_command = xml_parser.get_command()
                        
                        # Extract file commands from the XML
                        commands = self._extract_file_commands(mcp_command)
                        
                        # Reset accumulated tokens after successful detection
                        accumulated_tokens = ""
                        
                        if commands:
                            # Execute the commands
                            print(
                                f"{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                                f"EXECUTING {len(commands)} MCP COMMANDS{Colors.ENDC}"
                            )
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
                            payload = {
                                "model": self.model,
                                "prompt": prompt,
                                "stream": True,
                            }
                            if system_prompt:
                                payload["system"] = system_prompt
                                
                            # Reset the XML parser for the continuation
                            xml_parser.reset()
                            
                            # Break out of the token loop to start a new request
                            break
                            
                    # Check accumulated tokens periodically for complete commands
                    if len(accumulated_tokens) > accumulated_tokens_max:
                        if (
                            "<mcp:filesystem>" in accumulated_tokens
                            and "</mcp:filesystem>" in accumulated_tokens
                        ):
                            # Use regex to find complete MCP blocks
                            mcp_blocks = re.findall(
                                r"<mcp:filesystem>.*?</mcp:filesystem>",
                                accumulated_tokens,
                                re.DOTALL,
                            )
                            
                            if mcp_blocks:
                                print(
                                    f"\n{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                                    f"MCP COMMAND FOUND IN ACCUMULATED TOKENS{Colors.ENDC}"
                                )
                                mcp_command = mcp_blocks[0]
                                
                                # Extract file commands from the XML
                                commands = self._extract_file_commands(mcp_command)
                                
                                # Reset accumulated tokens after successful detection
                                accumulated_tokens = ""
                                
                                if commands:
                                    # Execute the commands
                                    print(
                                        f"{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                                        f"EXECUTING {len(commands)} MCP COMMANDS{Colors.ENDC}"
                                    )
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
                                    payload = {
                                        "model": self.model,
                                        "prompt": prompt,
                                        "stream": True,
                                    }
                                    if system_prompt:
                                        payload["system"] = system_prompt
                                        
                                    # Reset the XML parser for the continuation
                                    xml_parser.reset()
                                    
                                    # Break out of the token loop to start a new request
                                    break
                                    
                        # Keep a sliding window of tokens
                        if len(accumulated_tokens) > accumulated_tokens_max * 2:
                            accumulated_tokens = accumulated_tokens[-accumulated_tokens_max:]
                            
                except Exception as e:
                    print(
                        f"{Colors.RED}TRANSIENT AGENT {self.task_id}: Error processing token: {str(e)}{Colors.ENDC}"
                    )
                    # Continue with next token
                    
            # Check for commands in the complete response before finishing
            if (
                has_completed
                and not need_continuation
                and "<mcp:filesystem>" in full_response
                and "</mcp:filesystem>" in full_response
            ):
                mcp_blocks = re.findall(
                    r"<mcp:filesystem>.*?</mcp:filesystem>", full_response, re.DOTALL
                )
                
                if mcp_blocks:
                    print(
                        f"\n{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                        f"FOUND {len(mcp_blocks)} MCP COMMANDS IN FINAL RESPONSE{Colors.ENDC}"
                    )
                    all_results = ""
                    
                    for idx, mcp_command in enumerate(mcp_blocks):
                        # Extract file commands from the XML
                        commands = self._extract_file_commands(mcp_command)
                        
                        if commands:
                            # Execute the commands
                            results = self._execute_file_commands(commands)
                            
                            # Format the results for display
                            result_output = self._format_command_results(results)
                            all_results += result_output
                            
                    if all_results:
                        full_response += "\n\n" + all_results
                        
            # If the model finished generating and we don't need continuation, we're done
            if has_completed and not need_continuation:
                should_continue = False
                
            # If we need to continue after a command, we'll make another request
            if need_continuation:
                # Reset for next cycle
                need_continuation = False
                if stream:
                    print(
                        f"\n{Colors.BG_GREEN}{Colors.BOLD}TRANSIENT AGENT {self.task_id}: "
                        f"CONTINUING GENERATION WITH COMMAND RESULTS{Colors.ENDC}\n"
                    )
                    
        print(
            f"{Colors.GREEN}TRANSIENT AGENT {self.task_id}: "
            f"Response complete ({len(full_response)} characters){Colors.ENDC}"
        )
        return full_response