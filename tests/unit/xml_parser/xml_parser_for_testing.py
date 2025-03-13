"""XML parser for MCP commands - test version with mock dependencies."""

import re
from tests.mocks.terminal_utils import Colors


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
            # Process self-closing and opening tags
            for match in re.finditer(r"<(\w+(?::\w+)?)(?: [^>]*)?(/?)>", self.buffer):
                tag = match.group(1)
                is_self_closing = match.group(2) == "/"

                if not is_self_closing and tag != "mcp:filesystem":  # avoid duplication for opening mcp tag
                    self.xml_stack.append(tag)
                    self.debug_print(f"Added tag to stack: {tag}, stack: {self.xml_stack}")

            # Match closing tags
            for match in re.finditer(r"</(\w+(?::\w+)?)>", self.buffer):
                tag = match.group(1)
                
                if self.xml_stack and self.xml_stack[-1] == tag:
                    self.xml_stack.pop()
                    self.debug_print(f"Popped tag from stack: {tag}, remaining: {self.xml_stack}")
                    
                    # Check if we've closed the MCP block
                    if not self.xml_stack and tag == "mcp:filesystem":
                        # We have a complete command
                        end_idx = match.end()
                        self.complete_command += self.buffer[:end_idx]
                        self.buffer = self.buffer[end_idx:]
                        self.in_mcp_block = False
                        self.debug_print(f"Complete command detected: {self.complete_command}")
                        return True

            # For testing purposes, we'll accumulate the buffer differently
            if not self.complete_command.endswith(self.buffer):
                self.complete_command += self.buffer
                
            # Keep a small sliding window to catch split tags
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

    def feed(self, token: str) -> bool:
        """
        Process a new token and update parser state.
        Returns True if a complete MCP command is detected.
        """
        # Store the buffer before adding the token for debugging
        old_buffer = self.buffer
        
        # Check for think blocks
        if "<think>" in token and not self.in_think_block:
            self.in_think_block = True
            think_start_pos = token.find("<think>")
            
            # If both opening and closing tags in same token
            if "</think>" in token[think_start_pos:]:
                self.in_think_block = False
                end_pos = token.find("</think>", think_start_pos) + len("</think>")
                
                # Only keep content outside think block
                token_to_process = token[:think_start_pos] + token[end_pos:]
                self.buffer += token_to_process
                self.debug_print("Think block in single token - processed")
            else:
                # Keep content before think block
                self.buffer += token[:think_start_pos]
                self.debug_print("Entered think block")
        elif "</think>" in token and self.in_think_block:
            self.in_think_block = False
            end_pos = token.find("</think>") + len("</think>")
            
            # Only keep content after think block
            self.buffer += token[end_pos:]
            self.debug_print("Exited think block")
        elif self.in_think_block:
            # Skip token if in think block
            self.debug_print("Inside think block - skipping")
            pass
        else:
            # Normal token processing
            self.buffer += token
        
        # Check for complete command detection methods
        
        # Method 1: Fast path - check if we have a complete mcp command in buffer
        if not self.in_mcp_block and "<mcp:filesystem>" in self.buffer and "</mcp:filesystem>" in self.buffer:
            commands = self.extract_complete_xml(self.buffer)
            if commands:
                self.complete_command = commands[0]
                self.buffer = self.buffer.replace(commands[0], "", 1)
                self.debug_print(f"Fast path detection: {commands[0]}")
                return True
                
        # Method 2: Step through XML parsing to detect commands
        if self.check_for_mcp_commands():
            return True
            
        # Method 3: Large buffer fallback
        if (len(self.buffer) > 200 and "<mcp:filesystem>" in self.buffer and "</mcp:filesystem>" in self.buffer):
            fallback_commands = self.extract_complete_xml(self.buffer)
            if fallback_commands:
                self.complete_command = fallback_commands[0]
                # Remove the extracted command from buffer
                start = self.buffer.find(fallback_commands[0])
                end = start + len(fallback_commands[0])
                self.buffer = self.buffer[:start] + self.buffer[end:]
                self.debug_print(f"Large buffer fallback: {fallback_commands[0]}")
                return True
                
        # No command detected
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
        self.partial_tag_buffer = ""