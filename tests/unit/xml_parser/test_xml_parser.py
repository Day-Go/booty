"""Unit tests for the StreamingXMLParser class."""

from src.utils.xml_parser import StreamingXMLParser


class TestStreamingXMLParser:
    """Test suite for the StreamingXMLParser class."""

    def setup_method(self):
        """Set up a fresh parser instance before each test."""
        self.parser = StreamingXMLParser(debug_mode=False)

    def test_initialization(self):
        """Test the parser initializes with correct default state."""
        assert self.parser.buffer == ""
        assert self.parser.complete_command == ""
        assert self.parser.in_think_block is False
        assert self.parser.in_code_block is False
        assert self.parser.code_block_lang is None
        assert self.parser.code_block_content == ""
        assert self.parser.debug_mode is False

    def test_reset(self):
        """Test the reset method clears parser state."""
        # Set up non-default state

        self.parser.buffer = "Theres content in the buffer"
        self.parser.complete_command = "get_working_dir"
        self.parser.in_think_block = False
        self.parser.in_code_block = True
        self.parser.code_block_lang = "Python"
        self.parser.code_block_content = "def main(): print('hello, world!')"

        # Reset the parser
        self.parser.reset()

        # Verify state was reset
        assert self.parser.buffer == ""
        assert self.parser.complete_command == ""
        assert self.parser.in_think_block is False
        assert self.parser.in_code_block is False
        assert self.parser.code_block_lang is None
        assert self.parser.code_block_content == ""

    def test_simple_mcp_command_detection(self):
        """Test detection of a simple MCP command."""
        command = "<mcp:filesystem><read path='/some/path' /></mcp:filesystem>"

        # Feed the command token by token
        self.parser.feed(command)

        # Now check if a command was detected
        assert self.parser.get_command() == command

    def test_think_block_filtering(self):
        """Test that content inside <think> blocks is ignored."""
        # Command with think block
        content = "Some text <think>This should be ignored <mcp:filesystem>inside think</mcp:filesystem></think> <mcp:filesystem><list path='/' /></mcp:filesystem>"

        # Feed the content token by token
        self.parser.feed(content)

        # The parser should detect the command outside the think block, not the one inside
        command = self.parser.get_command()
        assert "<list path='/' />" in command
        assert "inside think" not in command

    def test_think_block_in_single_token(self):
        """Test handling of a think block that opens and closes in a single token."""
        # Feed a token with a complete think block
        self.parser.feed(
            "<think>ignore this</think><mcp:filesystem><pwd /></mcp:filesystem>"
        )

        # The parser should detect the command after the think block
        command = self.parser.get_command()
        assert "<pwd />" in command
        assert "ignore this" not in command

    def test_partial_command_detection(self):
        """Test detection of a command that comes in multiple chunks."""
        # Feed first part
        self.parser.feed("<mcp:filesystem><read ")
        
        # The parser now uses a buffer approach rather than an XML stack
        # Since no complete command is found yet, buffer should contain the partial command
        assert "<mcp:filesystem><read " in self.parser.buffer
        
        # Feed second part
        self.parser.feed("path='/some/file.txt' /></mcp:filesystem>")

        # Now we should have a complete command
        command = self.parser.get_command()
        assert (
            "<mcp:filesystem><read path='/some/file.txt' /></mcp:filesystem>" == command
        )

    def test_nested_tags(self):
        """Test handling of nested XML tags."""
        command = "<mcp:filesystem><write path='/test.txt'>content with <b>bold</b> text</write></mcp:filesystem>"

        # Feed the command character by character
        self.parser.feed(command)

        assert self.parser.get_command() == command

    def test_extract_complete_xml_fallback(self):
        """Test the fallback mechanism for extracting complete XML."""
        text = "Some text before <mcp:filesystem><read path='/file.txt' /></mcp:filesystem> and after"
        commands = self.parser.extract_complete_xml(text)

        assert len(commands) == 1
        assert (
            commands[0] == "<mcp:filesystem><read path='/file.txt' /></mcp:filesystem>"
        )

    def test_multiple_commands(self):
        """Test handling of multiple consecutive commands."""
        # Feed first command
        command1 = "<mcp:filesystem><get_working_directory /></mcp:filesystem>"
        command2 = "<mcp:filesystem><list path='/' /></mcp:filesystem>"

        # Feed first command
        first_result = self.parser.feed(command1)
        assert first_result is True
        
        # Get first command
        first_command = self.parser.get_command()
        assert first_command == command1
        
        # Feed second command separately
        second_result = self.parser.feed(command2)
        assert second_result is True
        
        # Get second command
        second_command = self.parser.get_command()
        assert second_command == command2

    def test_self_closing_tags(self):
        """Test proper handling of self-closing tags."""
        command = "<mcp:filesystem><read path='/file.txt' /><get_working_directory /></mcp:filesystem>"

        # Feed the command character by character
        self.parser.feed(command)

        assert self.parser.get_command() == command

    def test_large_buffer_fallback(self):
        """Test fallback detection for large buffers."""
        # Create a buffer larger than 200 chars with a complete command
        prefix = "x" * 100
        command = "<mcp:filesystem><read path='/file.txt' /></mcp:filesystem>"
        suffix = "y" * 100

        content = prefix + command + suffix

        # Feed the content in one go
        self.parser.feed(content)

        # The parser should detect the command using the fallback mechanism
        detected_command = self.parser.get_command()
        assert detected_command == command

    def test_multiple_commands_in_buffer(self):
        """Test handling of multiple commands in the buffer."""
        content = (
            "<mcp:filesystem><get_working_directory /></mcp:filesystem> "
            "Some text between commands "
            "<mcp:filesystem><list path='/' /></mcp:filesystem>"
        )

        # Feed the content in one go
        self.parser.feed(content)

        # First command should be detected
        first_command = self.parser.get_command()
        assert "<get_working_directory />" in first_command
        
        # The current implementation processes one command at a time
        # We need to manually check for additional commands in the buffer
        has_more = self.parser.check_for_mcp_commands()
        assert has_more is True
        
        # Second command should now be detected
        second_command = self.parser.get_command()
        assert "<list path='/' />" in second_command

    def test_malformed_xml_handling(self):
        """Test how the parser handles malformed XML."""
        # XML with unclosed tag - missing the closing read tag
        content = "<mcp:filesystem><read path='/file.txt'></mcp:filesystem>"

        # We first feed the content to extract it from the buffer
        self.parser.feed(content)
        
        # In the current implementation, the malformed XML is extracted
        # but then fails validation in parse_xml
        command = self.parser.get_command()
        
        # The command should be extracted
        assert command == content
        
        # Validate directly using parse_xml
        is_valid = self.parser.parse_xml(content)
        
        # The XML should be invalid
        assert is_valid is False

    def test_attributes_with_quotes(self):
        """Test handling of attributes with quotes."""
        command = "<mcp:filesystem><grep path='/src' pattern='function name=\"test\"' /></mcp:filesystem>"

        # Feed the command character by character
        self.parser.feed(command)

        assert self.parser.get_command() == command

    def test_xml_in_code_block(self):
        """Test extracting XML commands from Markdown code blocks."""
        # Command wrapped in a code block with xml language specifier
        code_block = (
            "```xml\n<mcp:filesystem><read path='/test.txt' /></mcp:filesystem>\n```"
        )

        # Feed the code block in one go
        self.parser.feed(code_block)

        # The parser should detect the command inside the code block
        command = self.parser.get_command()
        assert "<read path='/test.txt' />" in command

    def test_xml_in_unspecified_code_block(self):
        """Test extracting XML commands from unspecified language code blocks."""
        # Command wrapped in a code block without language specifier
        code_block = "```\n<mcp:filesystem><list path='/' /></mcp:filesystem>\n```"

        # Feed the code block in one go
        self.parser.feed(code_block)

        # The parser should detect the command inside the code block
        command = self.parser.get_command()
        assert "<list path='/' />" in command
