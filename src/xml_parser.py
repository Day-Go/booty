"""XML parser for MCP commands."""

import re

# Use try-except for imports to handle both direct module execution and package imports
try:
    # Try relative import first (for when running as a module)
    from terminal_utils import Colors
except ImportError:
    # Fall back to absolute import (for when imported from tests)
    from src.terminal_utils import Colors


class StreamingXMLParser:
    """Improved streaming parser for XML-based MCP commands"""

    def __init__(self, debug_mode=False):
        # Parser state
        self.in_mcp_block = False
        self.buffer = ""
        self.xml_stack = []
        self.complete_command = ""
        self.in_think_block = False
        self.debug_mode = debug_mode
        self.partial_tag_buffer = ""
        self.in_code_block = False
        self.code_block_lang = None
        self.code_block_content = ""

    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"{Colors.BG_YELLOW}{Colors.BOLD}XML PARSER:{Colors.ENDC} {message}")

    def check_for_mcp_commands(self) -> bool:
        """Check the buffer for complete MCP commands"""
        # Look for opening MCP tag
        if "<mcp:filesystem>" in self.buffer and not self.in_mcp_block:
            self.in_mcp_block = True
            self.xml_stack.append("mcp:filesystem")
            self.complete_command = "<mcp:filesystem>"
            # Remove everything before the opening tag
            start_idx = self.buffer.find("<mcp:filesystem>") + len("<mcp:filesystem>")
            self.buffer = self.buffer[start_idx:]
            self.debug_print(f"Found opening MCP tag, buffer now: '{self.buffer}'")

        # Process MCP block content if we're in one
        if self.in_mcp_block:
            # More robust tag detection with better regex for both self-closing and opening tags
            for match in re.finditer(r"<(\w+(?::\w+)?)(?: [^>]*)?(/?)>", self.buffer):
                tag = match.group(1)
                is_self_closing = match.group(2) == "/"

                if not is_self_closing:
                    self.xml_stack.append(tag)
                    self.debug_print(
                        f"Added tag to stack: {tag}, stack: {self.xml_stack}"
                    )

            # Match closing tags
            for match in re.finditer(r"</(\w+(?::\w+)?)>", self.buffer):
                tag = match.group(1)

                if self.xml_stack and self.xml_stack[-1] == tag:
                    self.xml_stack.pop()
                    self.debug_print(
                        f"Popped tag from stack: {tag}, remaining: {self.xml_stack}"
                    )

                    # Check if we've closed the MCP block
                    if not self.xml_stack and tag == "mcp:filesystem":
                        # We have a complete command
                        end_idx = match.end()
                        self.complete_command += self.buffer[:end_idx]
                        self.buffer = self.buffer[end_idx:]
                        self.in_mcp_block = False
                        self.debug_print(
                            f"Complete command detected: {self.complete_command}"
                        )
                        return True

            # Accumulate buffer but keep a small sliding window to catch split tags
            self.complete_command += self.buffer
            window_size = 50  # Larger window to catch split tags
            if len(self.buffer) > window_size:
                self.buffer = self.buffer[-window_size:]

        return False

    def extract_complete_xml(self, text: str) -> list:
        """Extract complete XML blocks as a fallback mechanism"""
        commands = []
        pattern = r"<mcp:filesystem>.*?</mcp:filesystem>"
        matches = re.findall(pattern, text, re.DOTALL)

        for match in matches:
            commands.append(match)

        return commands

    def check_for_code_blocks(self, combined: str) -> bool:
        """
        Check for code blocks in the input and extract XML commands from them.
        Returns True if a complete MCP command is found in a code block.
        """
        # Check for code block start
        if not self.in_code_block and "```" in combined:
            start_pos = combined.find("```")
            # Check if there's a language specifier
            lang_match = re.search(r"```(\w+)", combined[start_pos:])
            if lang_match:
                self.code_block_lang = lang_match.group(1)
                self.debug_print(
                    f"Found code block with language: {self.code_block_lang}"
                )
            else:
                self.code_block_lang = None
                self.debug_print("Found code block without language specifier")

            self.in_code_block = True

            # Extract content after the opening ```
            if lang_match:
                start_content = start_pos + len("```") + len(self.code_block_lang)
            else:
                start_content = start_pos + len("```")

            self.code_block_content = combined[start_content:]
            self.debug_print(
                f"Code block start detected, content so far: {self.code_block_content[:20]}..."
            )

        # Check for code block end
        if self.in_code_block and "```" in self.code_block_content:
            end_pos = self.code_block_content.find("```")
            full_content = self.code_block_content[:end_pos]
            self.debug_print(
                f"Code block end detected, full content: {full_content[:30]}..."
            )

            # If it's an XML code block or contains MCP commands, process it
            if self.code_block_lang == "xml" or "<mcp:filesystem>" in full_content:
                self.debug_print(
                    f"Found potential XML command in code block: {full_content}"
                )

                # Extract MCP commands from the code block
                if (
                    "<mcp:filesystem>" in full_content
                    and "</mcp:filesystem>" in full_content
                ):
                    commands = self.extract_complete_xml(full_content)
                    if commands:
                        self.complete_command = commands[0]
                        self.debug_print(
                            f"Extracted XML command from code block: {self.complete_command}"
                        )
                        self.in_code_block = False
                        self.code_block_content = ""
                        self.code_block_lang = None
                        return True

            # Reset code block state if no commands found
            self.in_code_block = False
            self.code_block_content = ""
            self.code_block_lang = None

        # If we're in code block, append to code block content
        if self.in_code_block:
            # We've already processed this token into code_block_content
            return False

        return False

    def feed(self, token: str) -> bool:
        """
        Process a new token and update parser state.
        Returns True if a complete MCP command is detected.
        """
        combined = self.buffer + token

        self.debug_print(f"Processing token: '{token}'")
        self.debug_print(f"Buffer before: '{self.buffer}'")
        self.debug_print(
            f"In think block: {self.in_think_block}, In MCP block: {self.in_mcp_block}, In code block: {self.in_code_block}"
        )

        # If we're in a code block, continue accumulating content
        if self.in_code_block:
            self.code_block_content += token

            # Check if this token completes a code block
            if "```" in self.code_block_content:
                end_pos = self.code_block_content.find("```")
                full_content = self.code_block_content[:end_pos]

                # If it's an XML code block, look for MCP commands
                if self.code_block_lang == "xml" or "<mcp:filesystem>" in full_content:
                    if (
                        "<mcp:filesystem>" in full_content
                        and "</mcp:filesystem>" in full_content
                    ):
                        commands = self.extract_complete_xml(full_content)
                        if commands:
                            self.complete_command = commands[0]
                            self.in_code_block = False
                            self.code_block_content = ""
                            self.code_block_lang = None
                            self.buffer += (
                                token  # Still add to buffer for normal processing
                            )
                            return True

                # Reset code block tracking
                self.in_code_block = False
                self.code_block_content = ""
                self.code_block_lang = None
            else:
                # Still in the code block, continue accumulating
                return False

        # Check for code block start
        if not self.in_code_block and "```" in token:
            # We might be starting a new code block
            start_pos = token.find("```")

            # Check if there's a language specifier
            lang_match = re.search(r"```(\w+)", token[start_pos:])
            if lang_match:
                self.code_block_lang = lang_match.group(1)
                self.debug_print(
                    f"Starting code block with language: {self.code_block_lang}"
                )

                # If it's an XML block, pay special attention
                if self.code_block_lang.lower() == "xml":
                    self.in_code_block = True
                    # Extract content after the opening marker
                    start_content = start_pos + len("```") + len(self.code_block_lang)
                    self.code_block_content = token[start_content:]

                    # If the code block might be completed in this token
                    if "```" in self.code_block_content:
                        cmd_result = self.check_for_code_blocks(token)
                        if cmd_result:
                            return True
            else:
                # No language specified, check if it has MCP commands
                after_marker = token[start_pos + 3 :]
                if "<mcp:filesystem>" in after_marker:
                    self.in_code_block = True
                    self.code_block_content = after_marker

                    # Check if the code block ends in this token
                    if "```" in self.code_block_content:
                        cmd_result = self.check_for_code_blocks(token)
                        if cmd_result:
                            return True

        # Improved think block handling with edge case detection
        if "<think>" in combined and not self.in_think_block:
            self.in_think_block = True
            # Store position to handle edge cases where both opening and closing tags are in same token
            think_start_pos = combined.find("<think>")

            # Check if think block closed in same token
            if "</think>" in combined[think_start_pos:]:
                self.in_think_block = False
                # Extract content between think tags
                end_pos = combined.find("</think>", think_start_pos) + len("</think>")
                # Only keep content outside of think block
                self.buffer = combined[:think_start_pos] + combined[end_pos:]
                self.debug_print("Think block opened and closed in same token")
                return self.check_for_mcp_commands()  # Check remaining content
            else:
                # Otherwise buffer the token and skip
                self.buffer += token
                self.debug_print("Entered think block")
                return False

        if "</think>" in combined and self.in_think_block:
            self.in_think_block = False
            # Only keep content after think block closes
            end_pos = combined.find("</think>") + len("</think>")
            self.buffer = combined[end_pos:]
            self.debug_print("Exited think block, checking remaining content")
            return self.check_for_mcp_commands()  # Check remaining content

        # If still in think block, just buffer and skip
        if self.in_think_block:
            self.buffer += token
            self.debug_print("Still in think block, skipping token")
            return False

        # Add token to buffer
        self.buffer += token

        # Try fallback direct extraction if buffer is large enough
        if (
            len(self.buffer) > 200
            and "<mcp:filesystem>" in self.buffer
            and "</mcp:filesystem>" in self.buffer
        ):
            fallback_commands = self.extract_complete_xml(self.buffer)
            if fallback_commands:
                self.debug_print(
                    f"Using fallback XML extraction, found: {fallback_commands[0]}"
                )
                self.complete_command = fallback_commands[0]
                # Remove the extracted command from buffer
                start = self.buffer.find(fallback_commands[0])
                end = start + len(fallback_commands[0])
                self.buffer = self.buffer[:start] + self.buffer[end:]
                return True

        # Regular processing for token-by-token detection
        result = self.check_for_mcp_commands()

        self.debug_print(f"Buffer after: '{self.buffer}'")
        self.debug_print(f"Command detected: {result}")

        return result

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
        self.partial_tag_buffer = ""
        self.in_code_block = False
        self.code_block_lang = None
        self.code_block_content = ""
