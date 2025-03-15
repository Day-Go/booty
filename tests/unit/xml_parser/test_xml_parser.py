"""Unit tests for the StreamingXMLParser class."""

import pytest
from tests.mocks.simplified_parser import StreamingXMLParser


class TestStreamingXMLParser:
    """Test suite for the StreamingXMLParser class."""

    def setup_method(self):
        """Set up a fresh parser instance before each test."""
        self.parser = StreamingXMLParser(debug_mode=False)

    def test_initialization(self):
        """Test the parser initializes with correct default state."""
        assert self.parser.in_mcp_block is False
        assert self.parser.buffer == ""
        assert self.parser.xml_stack == []
        assert self.parser.complete_command == ""
        assert self.parser.in_think_block is False
        assert self.parser.partial_tag_buffer == ""

    def test_reset(self):
        """Test the reset method clears parser state."""
        # Set up non-default state
        self.parser.in_mcp_block = True
        self.parser.buffer = "some buffer content"
        self.parser.xml_stack = ["tag1", "tag2"]
        self.parser.complete_command = "completed command"
        self.parser.in_think_block = True
        self.parser.partial_tag_buffer = "partial tag"

        # Reset the parser
        self.parser.reset()

        # Verify state was reset
        assert self.parser.in_mcp_block is False
        assert self.parser.buffer == ""
        assert self.parser.xml_stack == []
        assert self.parser.complete_command == ""
        assert self.parser.in_think_block is False
        assert self.parser.partial_tag_buffer == ""

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
        assert self.parser.in_mcp_block is True
        assert (
            len(self.parser.xml_stack) == 2
        )  # Should have mcp:filesystem and read tags

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
        command1 = "<mcp:filesystem><pwd /></mcp:filesystem>"
        command2 = "<mcp:filesystem><list path='/' /></mcp:filesystem>"

        # Feed both commands
        self.parser.feed(command1 + " " + command2)

        # Get first command
        first_command = self.parser.get_command()
        assert first_command == command1

        # Get second command
        second_command = self.parser.get_command()
        assert second_command == command2

    def test_self_closing_tags(self):
        """Test proper handling of self-closing tags."""
        command = "<mcp:filesystem><read path='/file.txt' /><pwd /></mcp:filesystem>"

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
            "<mcp:filesystem><pwd /></mcp:filesystem> "
            "Some text between commands "
            "<mcp:filesystem><list path='/' /></mcp:filesystem>"
        )

        # Feed the content in one go
        self.parser.feed(content)

        # First command should be detected
        first_command = self.parser.get_command()
        assert "<pwd />" in first_command

        # Second command should also be detected
        second_command = self.parser.get_command()
        assert "<list path='/' />" in second_command

    def test_malformed_xml_handling(self):
        """Test how the parser handles malformed XML."""
        # XML with unclosed tag
        content = "<mcp:filesystem><read path='/file.txt'></mcp:filesystem>"

        # Feed the content token by token
        self.parser.feed(content)

        # The parser should have detected a command but XML stack may not be empty
        command = self.parser.get_command()
        assert command == content

        # Check parser state is reset
        assert self.parser.in_mcp_block is False

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

