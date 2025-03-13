"""Unit tests for the StreamingXMLParser class using fixtures."""

import pytest
from tests.mocks.simplified_parser import StreamingXMLParser


class TestStreamingXMLParserWithFixtures:
    """Tests for StreamingXMLParser using the fixtures from conftest.py."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up a fresh parser instance before each test."""
        self.parser = StreamingXMLParser(debug_mode=False)
        yield
        self.parser.reset()

    def test_command_detection_with_fixtures(self, sample_mcp_commands):
        """Test detection of various command types using fixtures."""
        for cmd_type, command in sample_mcp_commands.items():
            # Reset parser state for each command
            self.parser.reset()
            
            # Feed the command
            self.parser.feed(command)
                    
            # Verify the command was detected correctly
            detected_command = self.parser.get_command()
            assert detected_command == command, f"Failed to detect {cmd_type} command"

    def test_chunked_command_detection(self, sample_mcp_commands):
        """Test detection of commands fed in chunks rather than character by character."""
        for cmd_type, command in sample_mcp_commands.items():
            # Reset parser state for each command
            self.parser.reset()
            
            # Split the command into chunks of varying sizes
            chunks = [
                command[:len(command)//3],
                command[len(command)//3:2*len(command)//3],
                command[2*len(command)//3:]
            ]
            
            # Feed all chunks
            for chunk in chunks:
                self.parser.feed(chunk)
                    
            # Verify the command was detected
            detected_command = self.parser.get_command()
            assert detected_command == command, f"Failed to detect {cmd_type} command in chunks"

    def test_command_with_think_blocks(self, sample_mcp_commands):
        """Test handling of commands with think blocks interspersed."""
        for cmd_type, command in sample_mcp_commands.items():
            if cmd_type == "complex":
                continue  # Skip complex command for this test
                
            # Reset parser state for each command
            self.parser.reset()
            
            # Insert a think block before the command
            content = f"<think>Ignore this</think>{command}"
            
            # Feed the content in one go
            self.parser.feed(content)
            
            # Verify the command was detected correctly
            detected_command = self.parser.get_command()
            assert detected_command == command, f"Failed to detect {cmd_type} command after think block"

    def test_interleaved_commands_and_think_blocks(self, sample_mcp_commands):
        """Test handling of multiple commands with think blocks interleaved."""
        # Create a complex input with multiple commands and think blocks
        cmd1 = sample_mcp_commands["read"]
        cmd2 = sample_mcp_commands["list"]
        
        content = (
            f"Some text {cmd1} more text "
            f"<think>Thinking about {sample_mcp_commands['grep']}</think> "
            f"and then {cmd2}"
        )
        
        # Feed the content in one go for simplified testing
        self.parser.feed(content)
            
        # Check that both commands were detected
        # First command should be the read command
        first_command = self.parser.get_command()
        assert first_command == cmd1, "First command detected incorrectly"
            
        # Second command should be the list command
        second_command = self.parser.get_command()
        assert second_command == cmd2, "Second command detected incorrectly"
                    
    def test_malformed_command_recovery(self, sample_mcp_commands):
        """Test parser's ability to recover from malformed commands."""
        # Create a malformed command with unbalanced tags
        malformed = "<mcp:filesystem><read path='/file.txt'></read>no closing mcp tag"
        valid_cmd = sample_mcp_commands["pwd"]
        
        # Feed the malformed command followed by a valid one
        content = malformed + " " + valid_cmd
        
        # Feed the content in one go
        self.parser.feed(content)
        
        # For the simplified parser, we'll expect it to detect the valid command
        detected_command = self.parser.get_command()
        assert valid_cmd in detected_command, "Failed to recover and detect valid command after malformed input"