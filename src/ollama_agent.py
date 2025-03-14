"""Ollama-based agent with MCP filesystem integration."""

import json
import re
import time
import xml.etree.ElementTree as ET
import requests
import tiktoken
from typing import Dict, List, Any, Optional, Union, Tuple

from terminal_utils import Colors
from mcp_filesystem_client import MCPFilesystemClient
from xml_parser import StreamingXMLParser
from mcp_command_handler import MCPCommandHandler
from context_summarizer import ContextSummarizer, apply_context_summarization


class OllamaAgent:
    def __init__(
        self,
        model="gemma3:27b",
        api_base="http://localhost:11434",
        mcp_fs_url="http://127.0.0.1:8000",
        max_context_tokens=8192,  # Limit for the large model (gemma3:27b)
        system_prompt=None,
        agent_id="MAIN_AGENT",
        summarizer_model="gemma3:12b",
        summarizer_max_tokens=32000,  # Higher limit for the smaller model (gemma3:12b)
        enable_context_summarization=True,
        tokenizer_name="cl100k_base",  # OpenAI's tokenizer works well for most LLMs
    ):
        self.model = model
        self.api_base = api_base
        self.conversation_history = []
        self.agent_id = agent_id

        # Initialize MCP command handler
        self.mcp_handler = MCPCommandHandler(agent_id=agent_id, mcp_fs_url=mcp_fs_url)
        self.mcp_handler.set_debug_colors(Colors.MAGENTA, Colors.BG_MAGENTA)

        # For backward compatibility - these will be removed in a future refactoring
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)

        # Track tool usage
        self.tool_usage = []

        # Context management
        self.max_context_tokens = max_context_tokens
        self.system_prompt = system_prompt
        
        # Set up tokenizer for accurate token counting
        self.tokenizer_name = tokenizer_name
        try:
            self.tokenizer = tiktoken.get_encoding(tokenizer_name)
            print(f"{Colors.CYAN}[{self.agent_id}] Using tiktoken {tokenizer_name} for accurate token counting{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.YELLOW}[{self.agent_id}] Warning: Could not load tiktoken: {str(e)}{Colors.ENDC}")
            print(f"{Colors.YELLOW}[{self.agent_id}] Falling back to character-based estimation{Colors.ENDC}")
            self.tokenizer = None
            
        # Fallback token estimation if tokenization fails
        self.token_estimate_ratio = 4  # Approximation: 1 token ≈ 4 characters for English text
        
        # Context summarization (multi-model orchestration)
        self.enable_context_summarization = enable_context_summarization
        self.context_was_summarized = False
        
        if enable_context_summarization:
            self.summarizer = ContextSummarizer(
                model=summarizer_model,
                api_base=api_base,
                max_context_tokens=summarizer_max_tokens,
                tokenizer_name=self.tokenizer_name
            )
        else:
            self.summarizer = None

        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}[{self.agent_id}] Agent initialized with {model}{Colors.ENDC}"
        )
        if enable_context_summarization:
            print(
                f"{Colors.MAGENTA}[{self.agent_id}] Context summarization enabled with {summarizer_model}{Colors.ENDC}"
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
            f"{Colors.BG_MAGENTA}{Colors.BOLD}[{self.agent_id}] Generating response{Colors.ENDC}"
        )

        endpoint = f"{self.api_base}/api/generate"

        # Build the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,  # Always stream for command detection
            "options": {"num_ctx": self.max_context_tokens},
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make the request to Ollama API
        response = requests.post(endpoint, json=payload, stream=True)
        response.raise_for_status()

        # Process the streaming response and handle MCP commands
        return self.mcp_handler.process_streaming_response(
            response.iter_lines(),
            self.model,
            self.api_base,
            prompt,
            system_prompt,
            stream,
        )

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

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string
        
        Uses tiktoken for accurate token counting or falls back to character-based estimation.
        """
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            try:
                # Use tiktoken for accurate counting
                tokens = self.tokenizer.encode(text)
                return len(tokens)
            except Exception as e:
                print(f"{Colors.YELLOW}[{self.agent_id}] Error counting tokens: {str(e)}{Colors.ENDC}")
                # Fall back to character estimation
                return len(text) // self.token_estimate_ratio
        else:
            # Fall back to character estimation
            return len(text) // self.token_estimate_ratio

    def _check_context_size(self, history: List[Dict[str, str]]) -> Tuple[bool, int, bool]:
        """Check if the current context size is approaching the token limit
        and apply summarization if necessary and enabled.

        Args:
            history: The conversation history to check

        Returns:
            Tuple of (is_near_limit, token_count, was_summarized)
        """
        # Combine all messages for token counting
        history_text = "\n\n".join([msg["content"] for msg in history])
        
        # Add system prompt if present
        full_text = history_text
        if self.system_prompt:
            full_text = self.system_prompt + "\n\n" + history_text
            
        # Count tokens accurately using tiktoken
        token_count = self._count_tokens(full_text)

        # Check if exceeding limit (90% of max context)
        is_near_limit = token_count > (self.max_context_tokens * 0.9)
        exceeds_limit = token_count > self.max_context_tokens
        was_summarized = False

        print(
            f"{Colors.CYAN}Accurate context size: {token_count} tokens "
            f"(limit: {self.max_context_tokens}){Colors.ENDC}"
        )

        # Apply summarization if enabled, available and needed
        if exceeds_limit and self.enable_context_summarization and self.summarizer:
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}[{self.agent_id}] Context size exceeds limit. "
                f"Applying summarization...{Colors.ENDC}"
            )
            
            # First check the current token count
            history_text = "\n\n".join([msg["content"] for msg in history])
            current_token_count = self._count_tokens(history_text)
            
            # Only proceed with summarization if there's enough history to make it worthwhile
            if len(history) >= 4:  # Need at least 4 messages (2 exchanges) to summarize
                # Use the smaller model to summarize the context
                # Make sure to pass the system prompt to be preserved
                summarized_history, was_summarized = self.summarizer.summarize_history(
                    history, 
                    preserve_recent=2,
                    system_prompt=self.system_prompt
                )
                
                # Check if summarization actually reduced token count
                if was_summarized:
                    summarized_text = "\n\n".join([msg["content"] for msg in summarized_history])
                    summarized_token_count = self._count_tokens(summarized_text)
                    
                    # Only use summarized history if it actually reduces token count
                    if summarized_token_count >= current_token_count:
                        print(f"{Colors.BG_RED}{Colors.BOLD}[{self.agent_id}] Summarization did not reduce token count. "
                              f"Original: {current_token_count}, Summarized: {summarized_token_count}. "
                              f"Keeping original context.{Colors.ENDC}")
                        was_summarized = False
            else:
                print(f"{Colors.YELLOW}[{self.agent_id}] Not enough history to summarize.{Colors.ENDC}")
                was_summarized = False
            
            if was_summarized:
                print(
                    f"{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Context summarized successfully. "
                    f"Reduced from {len(history)} messages to {len(summarized_history)} messages.{Colors.ENDC}"
                )
                
                # Verify the summarized history is actually smaller
                summarized_text = "\n\n".join([msg["content"] for msg in summarized_history])
                summarized_token_count = self._count_tokens(summarized_text)
                
                if summarized_token_count < token_count:
                    # Update the conversation history with the summarized version
                    self.conversation_history = summarized_history
                    self.context_was_summarized = True
                    
                    # Update token count
                    token_count = summarized_token_count
                    
                    # Re-check limits after summarization
                    is_near_limit = token_count > (self.max_context_tokens * 0.9)
                else:
                    print(f"{Colors.BG_RED}{Colors.BOLD}[{self.agent_id}] Warning: Summarization increased token count "
                          f"from {token_count} to {summarized_token_count}. Using original context.{Colors.ENDC}")
                    was_summarized = False
                
                print(
                    f"{Colors.CYAN}New context size after summarization: {token_count} tokens "
                    f"(limit: {self.max_context_tokens}){Colors.ENDC}"
                )
            else:
                print(
                    f"{Colors.BG_RED}{Colors.BOLD}[{self.agent_id}] Context summarization failed. "
                    f"Proceeding with original context.{Colors.ENDC}"
                )
        elif is_near_limit:
            print(
                f"{Colors.BG_RED}{Colors.BOLD}WARNING: Context size is approaching the limit!{Colors.ENDC}"
            )

        return is_near_limit, token_count, was_summarized

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
        # Count tokens accurately
        if not self.conversation_history:
            token_count = 0
            if self.system_prompt:
                token_count = self._count_tokens(self.system_prompt)
        else:
            # Note we ignore the summarization result here as we just want the token count
            _, token_count, _ = self._check_context_size(self.conversation_history)

        status = {
            "messages": len(self.conversation_history),
            "exchanges": len(self.conversation_history) // 2,
            "token_count": token_count,
            "max_tokens": self.max_context_tokens,
            "usage_percentage": token_count / self.max_context_tokens * 100,
            "main_model": self.model,
            "tokenizer": self.tokenizer_name if hasattr(self, 'tokenizer_name') else "character-based estimation"
        }
        
        # Add summarization info if enabled
        if self.enable_context_summarization and self.summarizer:
            status.update({
                "summarization_enabled": True,
                "summarizer_model": self.summarizer.model,
                "summarizer_max_tokens": self.summarizer.max_context_tokens,
                "was_summarized": self.context_was_summarized
            })
        else:
            status.update({"summarization_enabled": False})
            
        return status

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
                # Build the status response
                status_response = (
                    f"Context Status:\n"
                    f"- Messages: {status['messages']} ({status['exchanges']} exchanges)\n"
                    f"- Token count: {status['token_count']:,} / {status['max_tokens']:,}\n"
                    f"- Context usage: {status['usage_percentage']:.1f}%\n"
                    f"- Main model: {status['main_model']}\n"
                    f"- Tokenizer: {status['tokenizer']}\n"
                )
                
                # Add summarization info if enabled
                if status.get('summarization_enabled', False):
                    status_response += (
                        f"\nContext Summarization:\n"
                        f"- Enabled: Yes\n"
                        f"- Summarizer model: {status['summarizer_model']}\n"
                        f"- Summarizer max tokens: {status['summarizer_max_tokens']:,}\n"
                        f"- Was context summarized: {'Yes' if status['was_summarized'] else 'No'}\n"
                    )
                else:
                    status_response += "\nContext Summarization: Disabled\n"
                
                status_response += (
                    f"\nAvailable commands:\n"
                    f"- /status - Show this status\n"
                    f"- /prune [n] - Keep only last n exchanges\n"
                    f"- /clear - Clear entire conversation history"
                )
                
                return status_response

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

        # Check context size before proceeding and apply summarization if needed
        is_near_limit, token_count, was_summarized = self._check_context_size(self.conversation_history)

        # Warn user if context is getting too large
        if is_near_limit and not was_summarized:
            warning = (
                f"\n{Colors.BG_RED}{Colors.BOLD}WARNING: Conversation context is getting large "
                f"({token_count:,} tokens, {token_count / self.max_context_tokens:.1%} of capacity). "
                f"Consider using /prune or /clear to manage context.{Colors.ENDC}\n"
            )
            print(warning)
        
        # If context was summarized, inform the user
        if was_summarized:
            print(
                f"\n{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Notice: The conversation history has been summarized "
                f"to fit within context limits. Some details from earlier messages may have been condensed.{Colors.ENDC}\n"
            )

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

        # Check context size again after adding response and potentially summarize
        is_near_limit, token_count, was_summarized = self._check_context_size(self.conversation_history)

        # If context was summarized, inform the user in the response
        if was_summarized:
            context_notice = (
                f"\n\n[NOTICE: The conversation history has been automatically summarized by {self.summarizer.model} "
                f"to fit within the context limit of {self.max_context_tokens} tokens. "
                f"Current context size: {token_count:,} tokens.]"
            )
            response += context_notice
        # If context is getting too large but wasn't summarized, append a warning
        elif is_near_limit:
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
