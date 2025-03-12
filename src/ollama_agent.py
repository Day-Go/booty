"""Ollama-based agent with MCP filesystem integration."""

import json
import re
import time
import xml.etree.ElementTree as ET
import requests
from typing import Dict, List, Any, Optional, Union, Tuple

from terminal_utils import Colors
from mcp_filesystem_client import MCPFilesystemClient
from xml_parser import StreamingXMLParser


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
            mcp_blocks = re.findall(
                r"<mcp:filesystem>(.*?)</mcp:filesystem>", cleaned_message, re.DOTALL
            )

            print(
                f"{Colors.MAGENTA}Found {len(mcp_blocks)} MCP filesystem blocks{Colors.ENDC}"
            )

            # Process each MCP block using XML parsing
            for block_idx, block in enumerate(mcp_blocks):
                print(
                    f"{Colors.MAGENTA}Processing MCP block #{block_idx + 1}:{Colors.ENDC}"
                )
                print(f"{Colors.MAGENTA}{block}{Colors.ENDC}")

                # Wrap the block in a root element for proper XML parsing
                xml_content = f"<root>{block}</root>"

                # Use a more permissive approach for handling potentially malformed XML
                try:
                    root = ET.fromstring(xml_content)

                    # Process each command element in the block
                    for cmd_element in root:
                        cmd_type = cmd_element.tag.lower()
                        print(
                            f"{Colors.MAGENTA}Processing command type: {cmd_type}{Colors.ENDC}"
                        )

                        # Convert XML elements to command dictionaries
                        if cmd_type == "read":
                            path = cmd_element.get("path", "")
                            if path:
                                print(
                                    f"{Colors.MAGENTA}Read command with path: {path}{Colors.ENDC}"
                                )
                                commands.append({"action": "read", "path": path})

                        elif cmd_type == "write":
                            path = cmd_element.get("path", "")
                            content = cmd_element.text if cmd_element.text else ""
                            if path:
                                print(
                                    f"{Colors.MAGENTA}Write command with path: {path}{Colors.ENDC}"
                                )
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
                                print(
                                    f"{Colors.MAGENTA}List command with path: {path}{Colors.ENDC}"
                                )
                                commands.append({"action": "list", "path": path})

                        elif cmd_type == "search":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                print(
                                    f"{Colors.MAGENTA}Search command with path: {path}, pattern: {pattern}{Colors.ENDC}"
                                )
                                commands.append(
                                    {
                                        "action": "search",
                                        "path": path,
                                        "pattern": pattern,
                                    }
                                )

                        elif cmd_type == "pwd":
                            print(f"{Colors.MAGENTA}PWD command{Colors.ENDC}")
                            commands.append({"action": "pwd"})

                        elif cmd_type == "grep":
                            path = cmd_element.get("path", "")
                            pattern = cmd_element.get("pattern", "")
                            if path and pattern:
                                print(
                                    f"{Colors.MAGENTA}Grep command with path: {path}, pattern: {pattern}{Colors.ENDC}"
                                )
                                commands.append(
                                    {"action": "grep", "path": path, "pattern": pattern}
                                )

                except Exception as xml_error:
                    print(
                        f"{Colors.RED}Error parsing XML: {str(xml_error)}{Colors.ENDC}"
                    )
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
                    content = cmd.get(
                        "content", "This is test content written by Ollama"
                    )
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
                    result_output += (
                        f"\n--- No grep matches for '{pattern}' in {path} ---\n---\n"
                    )

        return result_output

    def _generate_raw_response(self, prompt, system_prompt=None, stream=True) -> str:
        """Generate a raw response from Ollama API with improved streaming command detection

        This method now:
        1. Streams tokens from the LLM with enhanced buffer management
        2. Monitors for complete MCP filesystem XML commands with more robust detection
        3. Interrupts generation when a command is detected
        4. Executes the command and injects the result
        5. Continues generation with the new context
        6. Includes fallback mechanisms for detecting complete commands

        If stream=True, it will stream the response to the console in real-time
        and handle MCP commands on-the-fly.
        """
        print(
            f"\n{Colors.BG_YELLOW}{Colors.BOLD}DEBUG: Getting raw response from Ollama{Colors.ENDC}"
        )
        print(f"{Colors.YELLOW}Prompt length: {len(prompt)} characters{Colors.ENDC}")

        endpoint = f"{self.api_base}/api/generate"

        # Build the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }  # Always stream for command detection

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make the request to Ollama API
        print(f"{Colors.YELLOW}Making request to Ollama API...{Colors.ENDC}")

        # Initialize the improved streaming parser with debug mode enabled
        xml_parser = StreamingXMLParser(debug_mode=True)

        # Initialize response tracking
        full_response = ""
        accumulated_tokens = ""  # For fallback detection
        should_continue = True
        has_completed = False

        # Track if we need to continue generation after command execution
        need_continuation = False

        # Maximum size before checking accumulated tokens for fallback detection
        accumulated_tokens_max = 500

        while should_continue:
            # Make the API request
            print(
                f"{Colors.YELLOW}Streaming response with improved command detection...{Colors.ENDC}"
            )
            response = requests.post(endpoint, json=payload, stream=True)
            response.raise_for_status()

            if not need_continuation:
                print("Response: ", end="", flush=True)

            # Process the streaming response token by token
            for line in response.iter_lines():
                if not line:
                    continue

                try:
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
                    accumulated_tokens += response_part

                    # Process token with enhanced XML parser
                    if xml_parser.feed(response_part):
                        # Complete MCP command detected - interrupt generation
                        print(
                            f"\n{Colors.BG_MAGENTA}{Colors.BOLD}MCP COMMAND DETECTED - INTERRUPTING GENERATION{Colors.ENDC}"
                        )

                        # Get the complete command
                        mcp_command = xml_parser.get_command()
                        print(
                            f"{Colors.MAGENTA}Complete command: {mcp_command}{Colors.ENDC}"
                        )

                        # Extract file commands from the XML
                        commands = self._extract_file_commands(mcp_command)

                        # Reset accumulated tokens after successful detection
                        accumulated_tokens = ""

                        if commands:
                            # Execute the commands
                            print(
                                f"{Colors.BG_BLUE}{Colors.BOLD}EXECUTING MCP COMMANDS{Colors.ENDC}"
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

                    # Fallback: Check accumulated tokens periodically for complete commands
                    # This helps catch commands that might be missed by token-by-token parsing
                    if len(accumulated_tokens) > accumulated_tokens_max:
                        if (
                            "<mcp:filesystem>" in accumulated_tokens
                            and "</mcp:filesystem>" in accumulated_tokens
                        ):
                            print(
                                f"\n{Colors.BG_YELLOW}{Colors.BOLD}CHECKING ACCUMULATED TOKENS FOR COMMANDS{Colors.ENDC}"
                            )

                            # Use regex to find complete MCP blocks
                            mcp_blocks = re.findall(
                                r"<mcp:filesystem>.*?</mcp:filesystem>",
                                accumulated_tokens,
                                re.DOTALL,
                            )

                            if mcp_blocks:
                                print(
                                    f"\n{Colors.BG_MAGENTA}{Colors.BOLD}MCP COMMAND FOUND IN ACCUMULATED TOKENS - INTERRUPTING{Colors.ENDC}"
                                )
                                mcp_command = mcp_blocks[0]
                                print(
                                    f"{Colors.MAGENTA}Complete command from accumulated: {mcp_command}{Colors.ENDC}"
                                )

                                # Extract file commands from the XML
                                commands = self._extract_file_commands(mcp_command)

                                # Reset accumulated tokens after successful detection
                                accumulated_tokens = ""

                                if commands:
                                    # Execute the commands
                                    print(
                                        f"{Colors.BG_BLUE}{Colors.BOLD}EXECUTING MCP COMMANDS{Colors.ENDC}"
                                    )
                                    results = self._execute_file_commands(commands)

                                    # Format the results for display
                                    result_output = self._format_command_results(
                                        results
                                    )

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

                        # If we didn't find a command, keep a sliding window of tokens
                        if len(accumulated_tokens) > accumulated_tokens_max * 2:
                            accumulated_tokens = accumulated_tokens[
                                -accumulated_tokens_max:
                            ]

                except Exception as e:
                    print(
                        f"\n{Colors.BG_RED}{Colors.BOLD}ERROR PROCESSING TOKEN: {str(e)}{Colors.ENDC}"
                    )
                    # Continue with next token

            # Final check for commands in the complete response before finishing
            if (
                has_completed
                and not need_continuation
                and "<mcp:filesystem>" in full_response
                and "</mcp:filesystem>" in full_response
            ):
                print(
                    f"\n{Colors.BG_YELLOW}{Colors.BOLD}FINAL CHECK FOR MISSED COMMANDS{Colors.ENDC}"
                )
                mcp_blocks = re.findall(
                    r"<mcp:filesystem>.*?</mcp:filesystem>", full_response, re.DOTALL
                )

                if mcp_blocks:
                    print(
                        f"\n{Colors.BG_MAGENTA}{Colors.BOLD}FOUND {len(mcp_blocks)} MCP COMMANDS IN FINAL RESPONSE{Colors.ENDC}"
                    )
                    all_results = ""

                    for idx, mcp_command in enumerate(mcp_blocks):
                        print(
                            f"{Colors.MAGENTA}Processing command {idx + 1}: {mcp_command}{Colors.ENDC}"
                        )

                        # Extract file commands from the XML
                        commands = self._extract_file_commands(mcp_command)

                        if commands:
                            # Execute the commands
                            print(
                                f"{Colors.BG_BLUE}{Colors.BOLD}EXECUTING MCP COMMAND {idx + 1}{Colors.ENDC}"
                            )
                            results = self._execute_file_commands(commands)

                            # Format the results for display
                            result_output = self._format_command_results(results)
                            all_results += result_output

                    if all_results:
                        print(
                            f"\n{Colors.BG_GREEN}{Colors.BOLD}APPENDING ALL RESULTS TO RESPONSE{Colors.ENDC}"
                        )
                        full_response += "\n\n" + all_results

            # If the model finished generating and we don't need continuation, we're done
            if has_completed and not need_continuation:
                should_continue = False

            # If we need to continue after a command, we'll make another request
            if need_continuation:
                # Reset for next cycle
                need_continuation = False
                print(
                    f"\n{Colors.BG_BLUE}{Colors.BOLD}CONTINUING GENERATION WITH COMMAND RESULTS{Colors.ENDC}\n"
                )

        # Final response
        print(
            f"{Colors.YELLOW}Response complete ({len(full_response)} characters){Colors.ENDC}"
        )
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