"""XML parser for MCP commands using xml.etree.ElementTree."""

import xml.etree.ElementTree as ET
from io import StringIO

try:
    from utils.terminal_utils import Colors
except ImportError:
    from src.utils.terminal_utils import Colors


class StreamingXMLParser:
    """Improved streaming parser for XML-based MCP commands using ElementTree"""

    def __init__(self, debug_mode=False):
        self.buffer = ""
        self.complete_command = ""
        self.in_think_block = False
        self.debug_mode = debug_mode
        self.in_code_block = False
        self.code_block_lang = None
        self.code_block_content = ""

    def debug_print(self, message):
        """Print debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"{Colors.BG_YELLOW}{Colors.BOLD}XML PARSER:{Colors.ENDC} {message}")

    def extract_complete_xml(self, text: str) -> list:
        """Extract complete XML blocks using ElementTree"""
        commands = []

        # Find all instances of complete MCP filesystem commands
        start_tag = "<mcp:filesystem>"
        end_tag = "</mcp:filesystem>"
        start_pos = 0

        while True:
            start_pos = text.find(start_tag, start_pos)
            if start_pos == -1:
                break

            end_pos = text.find(end_tag, start_pos)
            if end_pos == -1:
                break

            # Include the end tag
            end_pos += len(end_tag)

            # Extract complete XML fragment
            xml_fragment = text[start_pos:end_pos]
            commands.append(xml_fragment)

            # Move past this command
            start_pos = end_pos

        return commands

    def parse_xml(self, xml_str: str):
        """
        Parse an XML string using ElementTree.
        This is used for validation and potentially for extracting structured data.
        """
        try:
            # Register the mcp namespace
            ET.register_namespace("mcp", "mcp")

            # Parse the XML
            xml_str = self._prepare_xml_for_parsing(xml_str)
            root = ET.fromstring(xml_str)

            # Successful parse means it's valid XML
            return True
        except ET.ParseError as e:
            self.debug_print(f"XML parse error: {e}")
            return False

    def _prepare_xml_for_parsing(self, xml_str: str) -> str:
        """
        Prepare XML string for parsing by ensuring the mcp namespace is properly defined.
        This handles cases where the namespace prefix is used without declaration.
        """
        if "<mcp:" in xml_str and "xmlns:mcp" not in xml_str:
            # Add namespace declaration to root element
            xml_str = xml_str.replace(
                "<mcp:filesystem>", "<mcp:filesystem xmlns:mcp='mcp'>"
            )
        return xml_str

    def check_for_code_blocks(self, text: str) -> bool:
        """
        Check for code blocks in the input and extract XML commands from them.
        Returns True if a complete MCP command is found in a code block.
        """
        if not self.in_code_block and "```" in text:
            start_pos = text.find("```")
            # Check if there's a language specifier
            import re

            lang_match = re.search(r"```(\w+)", text[start_pos:])

            if lang_match:
                self.code_block_lang = lang_match.group(1)
                self.debug_print(
                    f"Found code block with language: {self.code_block_lang}"
                )
                # Extract content after the opening ```
                start_content = start_pos + len("```") + len(self.code_block_lang)
            else:
                self.code_block_lang = None
                self.debug_print("Found code block without language specifier")
                start_content = start_pos + len("```")

            self.in_code_block = True
            self.code_block_content = text[start_content:]

        # Check for code block end
        if self.in_code_block and "```" in self.code_block_content:
            end_pos = self.code_block_content.find("```")
            full_content = self.code_block_content[:end_pos]

            # If it's an XML code block or contains MCP commands, process it
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
                        return True

            # Reset code block state if no commands found
            self.in_code_block = False
            self.code_block_content = ""
            self.code_block_lang = None

        return False

    def check_for_mcp_commands(self) -> bool:
        """Check the buffer for complete MCP commands using ElementTree"""
        if "<mcp:filesystem>" in self.buffer and "</mcp:filesystem>" in self.buffer:
            commands = self.extract_complete_xml(self.buffer)

            if commands:
                # Get the first complete command
                self.complete_command = commands[0]

                # Remove the processed command from the buffer
                start_idx = self.buffer.find(self.complete_command)
                end_idx = start_idx + len(self.complete_command)
                self.buffer = self.buffer[:start_idx] + self.buffer[end_idx:]

                # Validate the XML structure
                if self.parse_xml(self.complete_command):
                    self.debug_print(
                        f"Valid MCP command found: {self.complete_command[:30]}..."
                    )
                    return True
                else:
                    self.debug_print("Invalid XML structure, discarding command")
                    self.complete_command = ""

        return False

    def handle_think_blocks(self, token: str) -> str:
        """
        Process think blocks and return the content that should be added to the buffer.
        """
        combined = self.buffer + token

        # Check for opening think tag
        if "<think>" in combined and not self.in_think_block:
            self.in_think_block = True
            think_start = combined.find("<think>")

            # Check if think block closed in same token
            if "</think>" in combined[think_start:]:
                self.in_think_block = False
                think_end = combined.find("</think>", think_start) + len("</think>")
                # Only return content outside the think block
                return combined[:think_start] + combined[think_end:]
            else:
                # In a think block but not closed yet
                return combined[:think_start]

        # Check for closing think tag
        if "</think>" in combined and self.in_think_block:
            self.in_think_block = False
            think_end = combined.find("</think>") + len("</think>")
            # Only return content after the think block
            return combined[think_end:]

        # If still in think block, discard this token
        if self.in_think_block:
            return self.buffer

        # Not in think block, return full token
        return combined

    def feed(self, token: str) -> bool:
        """
        Process a new token and update parser state.
        Returns True if a complete MCP command is detected.
        """
        self.debug_print(f"Processing token: '{token}'")
        self.debug_print(f"Buffer before: '{self.buffer}'")

        # First check for think blocks
        processed_content = self.handle_think_blocks(token)

        # Don't continue processing if we're in a think block
        if self.in_think_block:
            self.buffer = processed_content
            return False

        # Direct parsing of complete commands
        combined = processed_content
        if "<mcp:filesystem>" in combined and "</mcp:filesystem>" in combined:
            commands = self.extract_complete_xml(combined)
            if commands:
                self.complete_command = commands[0]

                # Remove the extracted command from buffer
                start = combined.find(commands[0])
                end = start + len(commands[0])
                self.buffer = combined[:start] + combined[end:]

                self.debug_print(
                    f"Found complete command: {self.complete_command[:30]}..."
                )
                return True

        # Check for code blocks
        if "```" in combined:
            if self.check_for_code_blocks(combined):
                return True

        # If we're in a code block, continue accumulating content
        if self.in_code_block:
            self.code_block_content += token

            # Check if this token completes a code block
            if "```" in self.code_block_content:
                if self.check_for_code_blocks(self.code_block_content):
                    return True

        # Update buffer with processed content
        self.buffer = processed_content

        # Check if buffer contains MCP commands
        return self.check_for_mcp_commands()

    def get_command(self) -> str:
        """Return the complete MCP command"""
        command = self.complete_command
        self.complete_command = ""
        return command

    def reset(self):
        """Reset parser state"""
        self.buffer = ""
        self.complete_command = ""
        self.in_think_block = False
        self.in_code_block = False
        self.code_block_lang = None
        self.code_block_content = ""

