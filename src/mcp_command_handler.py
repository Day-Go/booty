"""Shared MCP command handling logic for agent implementations."""

import re
import json
import requests
from typing import Dict, List, Any, Optional, Tuple

# Use try-except for imports to handle both direct module execution and package imports
try:
    # Try relative imports first (for when running as a module)
    from terminal_utils import Colors
    from mcp_filesystem_client import MCPFilesystemClient
    from xml_parser import StreamingXMLParser
except ImportError:
    # Fall back to absolute imports (for when imported from tests)
    from src.terminal_utils import Colors
    from src.mcp_filesystem_client import MCPFilesystemClient
    from src.xml_parser import StreamingXMLParser


class MCPCommandHandler:
    """Base class for handling MCP commands in agent implementations."""

    def __init__(self, agent_id: str, mcp_fs_url: str = "http://127.0.0.1:8000"):
        """Initialize the MCP command handler.

        Args:
            agent_id: Identifier for the agent using this handler
            mcp_fs_url: URL of the MCP filesystem server
        """
        self.agent_id = agent_id
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        self.debug_color = Colors.MAGENTA  # Default color for debug output
        self.debug_bg_color = Colors.BG_MAGENTA  # Default background color

    def set_debug_colors(self, text_color: str, bg_color: str):
        """Set debug output colors for this handler.

        Args:
            text_color: ANSI color code for text
            bg_color: ANSI color code for background
        """
        self.debug_color = text_color
        self.debug_bg_color = bg_color

    def debug_print(self, message: str, highlight: bool = False):
        """Print a debug message with agent-specific coloring.

        Args:
            message: The message to print
            highlight: Whether to use background color for emphasis
        """
        if highlight:
            print(
                f"{self.debug_bg_color}{Colors.BOLD}[{self.agent_id}] {message}{Colors.ENDC}"
            )
        else:
            print(f"{self.debug_color}[{self.agent_id}] {message}{Colors.ENDC}")

    def extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message using XML format.

        Args:
            message: Message containing potential commands

        Returns:
            List of command dictionaries
        """
        # Remove thinking blocks to avoid processing commands in thinking
        cleaned_message = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL)
        self.debug_print(
            f"Extracting commands from cleaned message ({len(cleaned_message)} chars)"
        )

        commands = []

        # Use XML parsing for command extraction
        try:
            # Find all <mcp:filesystem> blocks in the message
            mcp_blocks = re.findall(
                r"<mcp:filesystem>(.*?)</mcp:filesystem>", cleaned_message, re.DOTALL
            )

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

                        elif cmd_type == "pwd":
                            self.debug_print("PWD command")
                            commands.append({"action": "pwd"})

                        elif cmd_type == "get_working_directory":
                            self.debug_print("Get working directory command")
                            commands.append({"action": "get_working_directory"})

                        elif cmd_type == "cd":
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

                except Exception as xml_error:
                    self.debug_print(
                        f"Error parsing XML: {str(xml_error)}", highlight=True
                    )

        except Exception as e:
            self.debug_print(f"Error extracting MCP commands: {str(e)}", highlight=True)

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
                self.debug_print(f"Potential direct file reference: {potential_file}")

                # Check if it looks like a file (has extension)
                if "." in potential_file:
                    self.debug_print(f"Adding direct file reference as read command")
                    commands.append({"action": "read", "path": potential_file})

        self.debug_print(f"Found {len(commands)} total commands")
        return commands

    def execute_file_commands(
        self, commands: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute file operation commands using MCP Filesystem Server.

        Args:
            commands: List of command dictionaries

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
                    content = cmd.get("content", "Default content from MCP command")
                    result = self.fs_client.write_file(path, content)
                    results.append(
                        {
                            "action": "write",
                            "path": path,
                            "success": result.get("success", False),
                        }
                    )

                elif action == "pwd":
                    result = self.fs_client.get_working_directory()
                    results.append(
                        {
                            "action": "pwd",
                            "success": True,
                            "current_dir": result.get("current_dir"),
                        }
                    )

                elif action == "get_working_directory":
                    result = self.fs_client.get_working_directory()
                    results.append(
                        {
                            "action": "get_working_directory",
                            "success": True,
                            "current_dir": result.get("current_dir"),
                            "script_dir": result.get("script_dir"),
                        }
                    )

                elif action == "cd":
                    result = self.fs_client.change_directory(path)
                    results.append(
                        {
                            "action": "cd",
                            "path": path,
                            "success": result.get("success", False),
                            "current_dir": result.get("current_dir"),
                            "previous_dir": result.get("previous_dir"),
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

    def format_command_results(self, results: List[Dict[str, Any]]) -> str:
        """Format command execution results for inclusion in model context.

        Args:
            results: List of result dictionaries

        Returns:
            Formatted string with results
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

            elif action == "get_working_directory":
                current_dir = result.get("current_dir", "")
                script_dir = result.get("script_dir", "")
                result_output += (
                    f"\n--- Working directory information ---\n"
                    f"Current directory: {current_dir}\n"
                    f"Script directory: {script_dir}\n---\n"
                )

            elif action == "cd":
                current_dir = result.get("current_dir", "")
                previous_dir = result.get("previous_dir", "")
                result_output += (
                    f"\n--- Directory changed ---\n"
                    f"From: {previous_dir}\n"
                    f"To: {current_dir}\n---\n"
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

    def process_streaming_response(
        self, response_stream, model, api_base, prompt, system_prompt=None, stream=True
    ):
        """Process a streaming response, detecting and handling MCP commands.

        Args:
            response_stream: Iterator of response chunks
            model: Model being used
            api_base: API base URL
            prompt: Current prompt
            system_prompt: Optional system prompt
            stream: Whether to stream output

        Returns:
            Full response with command results
        """

        # Initialize the streaming parser
        xml_parser = StreamingXMLParser(debug_mode=False)

        # Initialize response tracking
        full_response = ""
        accumulated_tokens = ""
        should_continue = True
        has_completed = False
        need_continuation = False
        command_count = 0
        continuation_attempts = 0
        max_continuation_attempts = 10  # Limit to prevent infinite loops

        # Maximum size before checking accumulated tokens for fallback detection
        accumulated_tokens_max = 500

        endpoint = f"{api_base}/api/generate"

        while should_continue:
            for line in response_stream:
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
                        command_count += 1
                        # Complete MCP command detected - interrupt generation
                        self.debug_print(
                            f"MCP COMMAND #{command_count} DETECTED - INTERRUPTING",
                            highlight=True,
                        )

                        # Get the complete command
                        mcp_command = xml_parser.get_command()
                        self.debug_print(f"Complete command: {mcp_command}")

                        # Extract file commands from the XML
                        commands = self.extract_file_commands(mcp_command)

                        # Reset accumulated tokens after successful detection
                        accumulated_tokens = ""

                        if commands:
                            # Execute the commands
                            self.debug_print(
                                f"EXECUTING {len(commands)} MCP COMMANDS",
                                highlight=True,
                            )
                            results = self.execute_file_commands(commands)

                            # Format the results for display
                            result_output = self.format_command_results(results)

                            # Keep track of command position before modifying full_response
                            command_position = full_response.rfind("<mcp:filesystem>")

                            # Replace the command with the result
                            if command_position > 0:
                                # Remove the command and replace with results
                                full_response = (
                                    full_response[:command_position].strip()
                                    + "\n\n"
                                    + result_output
                                )
                            else:
                                # Add results to full response (fallback)
                                full_response += "\n" + result_output

                            if stream:
                                print(f"\n{result_output}")

                            # Set up for continuation
                            need_continuation = True

                            # Update the prompt with results for continuation and explicit command data
                            # Note that we've already replaced the command with results in full_response
                            # We ensure both the command results and an explicit reminder are included

                            continuation_prompt = (
                                f"{prompt}\n\nAI: {full_response}\n\n"
                                f"[System Message]\nIMPORTANT: I executed your MCP command. "
                                f"ONLY use the command results above, do not hallucinate or invent file structures. "
                                f"Examine the file list or command output carefully before continuing. "
                                f"Continue your analysis, examining these EXACT results, and run additional MCP commands "
                                f"if needed. Complete the entire task without asking the user for permission to continue.\n\n"
                                f"Command result summary: {result_output[:300]}...\n"
                            )

                            # Build the request payload for continuation
                            payload = {
                                "model": model,
                                "prompt": continuation_prompt,
                                "stream": True,
                            }
                            if system_prompt:
                                payload["system"] = system_prompt

                            # Reset the XML parser for the continuation
                            xml_parser.reset()

                            # Track continuation attempts
                            continuation_attempts += 1

                            if continuation_attempts > max_continuation_attempts:
                                self.debug_print(
                                    "REACHED MAXIMUM CONTINUATION ATTEMPTS - STOPPING",
                                    highlight=True,
                                )
                                full_response += "\n\n[Reached maximum number of command executions. Please ask a follow-up question to continue.]"
                                should_continue = False
                                break

                            self.debug_print(
                                f"Making continuation request with command results (attempt {continuation_attempts}/{max_continuation_attempts})",
                                highlight=True,
                            )

                            # Make a new request for continuation
                            response = requests.post(
                                endpoint, json=payload, stream=True
                            )
                            response.raise_for_status()
                            response_stream = response.iter_lines()

                            # Break out of current token processing to start with new response
                            break

                    # Fallback: Check accumulated tokens periodically for complete commands
                    if len(accumulated_tokens) > accumulated_tokens_max:
                        if (
                            "<mcp:filesystem>" in accumulated_tokens
                            and "</mcp:filesystem>" in accumulated_tokens
                        ):
                            self.debug_print("CHECKING ACCUMULATED TOKENS FOR COMMANDS")

                            # Use regex to find complete MCP blocks
                            mcp_blocks = re.findall(
                                r"<mcp:filesystem>.*?</mcp:filesystem>",
                                accumulated_tokens,
                                re.DOTALL,
                            )

                            if mcp_blocks:
                                command_count += 1
                                self.debug_print(
                                    f"MCP COMMAND #{command_count} FOUND IN ACCUMULATED TOKENS",
                                    highlight=True,
                                )
                                mcp_command = mcp_blocks[0]

                                # Extract file commands from the XML
                                commands = self.extract_file_commands(mcp_command)

                                # Reset accumulated tokens after successful detection
                                accumulated_tokens = ""

                                if commands:
                                    # Execute the commands
                                    self.debug_print(
                                        f"EXECUTING {len(commands)} MCP COMMANDS",
                                        highlight=True,
                                    )
                                    results = self.execute_file_commands(commands)

                                    # Format the results for display
                                    result_output = self.format_command_results(results)

                                    # Keep track of command position before modifying full_response
                                    command_position = full_response.rfind(
                                        "<mcp:filesystem>"
                                    )

                                    # Replace the command with the result
                                    if command_position > 0:
                                        # Remove the command and replace with results
                                        full_response = (
                                            full_response[:command_position].strip()
                                            + "\n\n"
                                            + result_output
                                        )
                                    else:
                                        # Add results to full response (fallback)
                                        full_response += "\n" + result_output

                                    if stream:
                                        print(f"\n{result_output}")

                                    # Set up for continuation
                                    need_continuation = True

                                    # Update the prompt with results for continuation and explicit command data
                                    # Note that we've already replaced the command with results in full_response
                                    # We ensure both the command results and an explicit reminder are included

                                    continuation_prompt = (
                                        f"{prompt}\n\nAI: {full_response}\n\n"
                                        f"[System Message]\nIMPORTANT: I executed your MCP command. "
                                        f"ONLY use the command results above, do not hallucinate or invent file structures. "
                                        f"Examine the file list or command output carefully before continuing. "
                                        f"Continue your analysis, examining these EXACT results, and run additional MCP commands "
                                        f"if needed. Complete the entire task without asking the user for permission to continue.\n\n"
                                        f"Command result summary: {result_output[:300]}...\n"
                                    )

                                    # Build the request payload for continuation
                                    payload = {
                                        "model": model,
                                        "prompt": continuation_prompt,
                                        "stream": True,
                                    }
                                    if system_prompt:
                                        payload["system"] = system_prompt

                                    # Reset the XML parser for the continuation
                                    xml_parser.reset()

                                    # Track continuation attempts
                                    continuation_attempts += 1

                                    if (
                                        continuation_attempts
                                        > max_continuation_attempts
                                    ):
                                        self.debug_print(
                                            "REACHED MAXIMUM CONTINUATION ATTEMPTS - STOPPING",
                                            highlight=True,
                                        )
                                        full_response += "\n\n[Reached maximum number of command executions. Please ask a follow-up question to continue.]"
                                        should_continue = False
                                        break

                                    self.debug_print(
                                        f"Making continuation request with command results (attempt {continuation_attempts}/{max_continuation_attempts})",
                                        highlight=True,
                                    )

                                    # Make a new request for continuation
                                    response = requests.post(
                                        endpoint, json=payload, stream=True
                                    )
                                    response.raise_for_status()
                                    response_stream = response.iter_lines()

                                    # Break out of current token processing to start with new response
                                    break

                        # If we didn't find a command, keep a sliding window of tokens
                        if len(accumulated_tokens) > accumulated_tokens_max * 2:
                            accumulated_tokens = accumulated_tokens[
                                -accumulated_tokens_max:
                            ]

                except Exception as e:
                    self.debug_print(
                        f"ERROR PROCESSING TOKEN: {str(e)}", highlight=True
                    )
                    # Continue with next token

            # Check for commands in the complete response before finishing
            # Important: process even if has_completed=False to handle incomplete responses with commands
            if (
                not need_continuation
                and "<mcp:filesystem>" in full_response
                and "</mcp:filesystem>" in full_response
            ):
                self.debug_print("FINAL CHECK FOR MISSED COMMANDS")

                mcp_blocks = re.findall(
                    r"<mcp:filesystem>.*?</mcp:filesystem>", full_response, re.DOTALL
                )

                if mcp_blocks:
                    self.debug_print(
                        f"FOUND {len(mcp_blocks)} MCP COMMANDS IN FINAL RESPONSE",
                        highlight=True,
                    )
                    all_results = ""

                    for idx, mcp_command in enumerate(mcp_blocks):
                        # Extract file commands from the XML
                        commands = self.extract_file_commands(mcp_command)

                        if commands:
                            # Execute the commands
                            self.debug_print(
                                f"EXECUTING COMMAND SET #{idx + 1}", highlight=True
                            )
                            results = self.execute_file_commands(commands)

                            # Format the results for display
                            result_output = self.format_command_results(results)
                            all_results += result_output

                    if all_results:
                        self.debug_print(
                            "APPENDING ALL RESULTS TO RESPONSE", highlight=True
                        )
                        # Replace the last command with results rather than just appending
                        command_position = full_response.rfind("<mcp:filesystem>")
                        if command_position > 0:
                            # Remove the command and replace with results
                            full_response = (
                                full_response[:command_position].strip()
                                + "\n\n"
                                + all_results
                            )
                        else:
                            # Add results to full response (fallback)
                            full_response += "\n\n" + all_results

                        # Set need_continuation flag to continue generation after command execution
                        need_continuation = True

                        # Update the prompt with results for continuation
                        continuation_prompt = (
                            f"{prompt}\n\nAI: {full_response}\n\n"
                            f"[System Message]\nIMPORTANT: I executed your MCP command. "
                            f"ONLY use the command results above, do not hallucinate or invent file structures. "
                            f"Examine the file list or command output carefully before continuing. "
                            f"Continue your analysis, examining these EXACT results, and run additional MCP commands "
                            f"if needed. Complete the entire task without asking the user for permission to continue.\n\n"
                            f"Command result summary: {all_results[:300]}...\n"
                        )

                        # Build the request payload for continuation
                        payload = {
                            "model": model,
                            "prompt": continuation_prompt,
                            "stream": True,
                        }
                        if system_prompt:
                            payload["system"] = system_prompt

                        # Reset the XML parser for the continuation
                        xml_parser.reset()

                        # Track continuation attempts
                        continuation_attempts += 1

                        if continuation_attempts > max_continuation_attempts:
                            self.debug_print(
                                "REACHED MAXIMUM CONTINUATION ATTEMPTS - STOPPING",
                                highlight=True,
                            )
                            full_response += "\n\n[Reached maximum number of command executions. Please ask a follow-up question to continue.]"
                            should_continue = False
                        else:
                            # Make a new request for continuation after final command
                            self.debug_print(
                                f"Making continuation request after final command (attempt {continuation_attempts}/{max_continuation_attempts})",
                                highlight=True,
                            )
                            response = requests.post(
                                endpoint, json=payload, stream=True
                            )
                            response.raise_for_status()
                            response_stream = response.iter_lines()

            # If the model finished generating and we don't need continuation, we're done
            if has_completed and not need_continuation:
                should_continue = False

            # If we need to continue after a command, we'll make another request
            if need_continuation:
                # Reset for next cycle
                need_continuation = False

                # Debug info about continuation
                self.debug_print(
                    f"CONTINUING GENERATION WITH COMMAND RESULTS (attempt {continuation_attempts}/{max_continuation_attempts})",
                    highlight=True,
                )

        self.debug_print(
            f"Response complete ({len(full_response)} characters, {command_count} MCP commands executed)"
        )
        return full_response
