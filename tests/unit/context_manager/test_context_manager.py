"""Unit tests for the ContextManager class."""

import pytest
from unittest.mock import patch, MagicMock
import re
from .context_manager_for_testing import ContextManager


class TestContextManager:
    """Test suite for the ContextManager class."""
    
    @pytest.fixture
    def context_manager(self):
        """Fixture providing a fresh context manager instance."""
        return ContextManager(max_context_tokens=1000, token_ratio=4)
    
    @pytest.fixture
    def sample_history(self):
        """Fixture providing a sample conversation history."""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, can you help me with a Python question?"},
            {"role": "assistant", "content": "Sure, I'd be happy to help with your Python question. What would you like to know?"},
            {"role": "user", "content": "How do I read a file in Python?"},
            {"role": "assistant", "content": "Reading a file in Python is straightforward. Here's how you can do it:\n\n```python\n# Open file and read contents\nwith open('filename.txt', 'r') as file:\n    content = file.read()\n    print(content)\n```\n\nThis will open the file in read mode, read all its contents, and then print them."}
        ]
    
    @pytest.fixture
    def large_history(self):
        """Fixture providing a large conversation history that would exceed context limits."""
        # Create a history with long messages to test pruning
        large_messages = []
        
        # System prompt
        large_messages.append({"role": "system", "content": "You are a helpful assistant that provides detailed responses."})
        
        # Add several user-assistant exchanges with increasingly large messages
        for i in range(5):
            # User message with 200 * (i+1) characters
            user_content = f"User question {i+1}: " + "x" * (200 * (i+1))
            large_messages.append({"role": "user", "content": user_content})
            
            # Assistant message with file operation results
            file_content = "file content " * 50  # 600 chars of file content
            assistant_content = (
                f"Here's my response to question {i+1}.\n\n"
                f"--- Content of file{i}.txt ---\n{file_content}\n---\n\n"
                f"Based on this file, I can tell you that..."
            )
            large_messages.append({"role": "assistant", "content": assistant_content})
        
        return large_messages
    
    @pytest.fixture
    def history_with_file_operations(self):
        """Fixture providing history with various file operation results embedded."""
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Show me the contents of test.py"},
            {"role": "assistant", "content": "Here's the content of the file:\n\n--- Content of test.py ---\nprint('Hello, world!')\n\ndef main():\n    print('This is a test')\n    \nif __name__ == '__main__':\n    main()\n---\n\nThis is a simple Python script that prints messages."},
            {"role": "user", "content": "List the files in the src directory"},
            {"role": "assistant", "content": "Here are the files in the src directory:\n\n--- Contents of directory /src ---\n- file1.py [1024 bytes]\n- file2.py [2048 bytes]\n- subfolder [dir]\n---\n\nThere are 2 Python files and 1 subfolder."},
            {"role": "user", "content": "Find all files containing 'error'"},
            {"role": "assistant", "content": "I searched for files containing 'error':\n\n--- Search results for 'error' in /src ---\n- file1.py: Contains 2 matches\n- logs/errors.log: Contains 15 matches\n---\n\nI found matches in 2 files."}
        ]
    
    def test_initialization(self, context_manager):
        """Test that the context manager initializes with correct parameters."""
        assert context_manager.max_context_tokens == 1000
        assert context_manager.token_ratio == 4
        assert context_manager.warning_threshold == 0.7
        assert context_manager.critical_threshold == 0.9
    
    def test_estimate_tokens(self, context_manager):
        """Test token estimation functionality."""
        text = "a" * 100  # 100 characters
        estimated_tokens = context_manager.estimate_tokens(text)
        assert estimated_tokens == 25  # 100 / 4 = 25 tokens
        
        # Test with empty string
        assert context_manager.estimate_tokens("") == 0
        
        # Test with different token ratios
        cm_ratio_5 = ContextManager(max_context_tokens=1000, token_ratio=5)
        assert cm_ratio_5.estimate_tokens(text) == 20  # 100 / 5 = 20 tokens
    
    @patch('builtins.print')
    def test_check_context_size_ok(self, mock_print, context_manager, sample_history):
        """Test context size checking with usage below warning threshold."""
        # Sample history should be well below the 70% threshold of 1000 tokens
        status, tokens, percentage = context_manager.check_context_size(sample_history)
        
        assert status == "ok"
        assert tokens < context_manager.max_context_tokens * context_manager.warning_threshold
        assert percentage < context_manager.warning_threshold
        mock_print.assert_called_once()
    
    @patch('builtins.print')
    def test_check_context_size_warning(self, mock_print, context_manager):
        """Test context size checking with usage above warning threshold but below critical."""
        # Create history that will be above 70% but below 90%
        # With token_ratio of 4, we need about 700-899 tokens = 2800-3596 chars
        history = [{"role": "user", "content": "x" * 3000}]  # ~750 tokens
        
        status, tokens, percentage = context_manager.check_context_size(history)
        
        assert status == "warning"
        assert tokens > context_manager.max_context_tokens * context_manager.warning_threshold
        assert tokens < context_manager.max_context_tokens * context_manager.critical_threshold
        assert percentage > context_manager.warning_threshold
        assert percentage < context_manager.critical_threshold
        mock_print.assert_called_once()
    
    @patch('builtins.print')
    def test_check_context_size_critical(self, mock_print, context_manager):
        """Test context size checking with usage above critical threshold."""
        # Create history that will be above 90% threshold
        # With token_ratio of 4, we need 900+ tokens = 3600+ chars
        history = [{"role": "user", "content": "x" * 4000}]  # 1000 tokens
        
        status, tokens, percentage = context_manager.check_context_size(history)
        
        assert status == "critical"
        assert tokens > context_manager.max_context_tokens * context_manager.critical_threshold
        assert percentage > context_manager.critical_threshold
        mock_print.assert_called_once()
    
    @patch('builtins.print')
    def test_check_context_size_with_system_prompt(self, mock_print, context_manager, sample_history):
        """Test that system prompt is included in context size calculations."""
        # First check without system prompt
        status_no_sys, tokens_no_sys, _ = context_manager.check_context_size(sample_history)
        
        # Then check with system prompt
        system_prompt = "You are a helpful assistant that provides accurate information." * 5  # Long prompt
        status_with_sys, tokens_with_sys, _ = context_manager.check_context_size(sample_history, system_prompt)
        
        # System prompt should add to the token count
        assert tokens_with_sys > tokens_no_sys
        
        # Calculate expected token increase
        expected_increase = len(system_prompt) // context_manager.token_ratio
        assert tokens_with_sys - tokens_no_sys == expected_increase
    
    @patch('builtins.print')
    def test_smart_prune_history_no_pruning_needed(self, mock_print, context_manager, sample_history):
        """Test that no pruning occurs when history is already below target percentage."""
        # Mock check_context_size to return values below target
        with patch.object(context_manager, 'check_context_size') as mock_check:
            mock_check.return_value = ("ok", 400, 0.4)  # Below the 0.6 default target
            
            pruned_history = context_manager.smart_prune_history(sample_history, target_percentage=0.6)
        
            # History should be unchanged
            assert pruned_history == sample_history
            assert len(pruned_history) == len(sample_history)
    
    @patch('builtins.print')
    def test_smart_prune_history_empty(self, mock_print, context_manager):
        """Test pruning empty history returns empty list."""
        result = context_manager.smart_prune_history([])
        assert result == []
    
    @patch('builtins.print')
    def test_smart_prune_history_file_operation_removal(self, mock_print, context_manager, history_with_file_operations):
        """Test that file operation results are removed during pruning."""
        # Set up context_manager to need pruning (history size > target)
        # We'll patch check_context_size to simulate this
        with patch.object(context_manager, 'check_context_size') as mock_check:
            # First call returns above target, subsequent calls return below target
            mock_check.side_effect = [
                ("warning", 800, 0.8),  # Initial check - above target
                ("ok", 500, 0.5)        # After file operation removal - below target
            ]
            
            pruned_history = context_manager.smart_prune_history(
                history_with_file_operations, target_percentage=0.6
            )
            
            # Check that pruning happened but length stayed the same
            assert len(pruned_history) == len(history_with_file_operations)
            
            # At least one of the assistant responses should have placeholder text
            assistant_responses = [msg["content"] for msg in pruned_history if msg["role"] == "assistant"]
            assert any("[File content removed during context pruning]" in resp or 
                   "[Directory listing removed during context pruning]" in resp or
                   "[Search results removed during context pruning]" in resp
                   for resp in assistant_responses)
    
    @patch('builtins.print')
    def test_smart_prune_history_message_summarization(self, mock_print, context_manager):
        """Test that long user messages are summarized during pruning."""
        # Create history with one very long user message (over 500 chars)
        long_message = "x" * 700
        history = [
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": long_message},  # Long message to be summarized
            {"role": "assistant", "content": "Here's my short response."},
            {"role": "user", "content": "Short recent message"},
            {"role": "assistant", "content": "Recent response"},
            {"role": "user", "content": "Final message"},
            {"role": "assistant", "content": "Final response"}
        ]
        
        # Mock check_context_size to simulate need for pruning after file op removal
        with patch.object(context_manager, 'check_context_size') as mock_check:
            mock_check.side_effect = [
                ("warning", 800, 0.8),  # Initial check - above target
                ("warning", 700, 0.7),  # After file operation removal - still above target
                ("ok", 500, 0.5)        # After message summarization - below target
            ]
            
            pruned_history = context_manager.smart_prune_history(history, target_percentage=0.6)
            
            # Check that message count is the same (no messages removed)
            assert len(pruned_history) == len(history)
            
            # Check that the long message was summarized (only for older messages, not recent ones)
            # The long message is not one of the last 4 messages, so it should be summarized
            assert len(pruned_history[1]["content"]) < len(long_message)
            assert "truncated" in pruned_history[1]["content"]
            
            # Recent messages should be unchanged
            assert pruned_history[-1]["content"] == "Final response"
            assert pruned_history[-2]["content"] == "Final message"
    
    @patch('builtins.print')
    def test_summarize_for_delegation(self, mock_print, context_manager, sample_history):
        """Test creating a summary for delegation to transient agent."""
        task_description = "Find information about Python file handling"
        
        # Modify history to ensure it ends with a user message
        if sample_history[-1]["role"] != "user":
            sample_history.append({"role": "user", "content": "How do I write to a file?"})
        
        # Generate summary
        summary = context_manager.summarize_for_delegation(
            sample_history, task_description, max_tokens=500
        )
        
        # Check that summary contains expected sections
        assert "# DELEGATED TASK" in summary
        assert task_description in summary
        
        # Should include the last user message
        assert "# CURRENT USER REQUEST" in summary
        assert sample_history[-1]["content"] in summary
        
        # Should include system prompt from first message
        assert "# SYSTEM PROMPT" in summary
        assert "You are a helpful assistant" in summary
        
        # Should include history section
        assert "# RELEVANT HISTORY" in summary
        
        # Length checks - should be less than max_tokens
        estimated_tokens = context_manager.estimate_tokens(summary)
        assert estimated_tokens <= 500
    
    @patch('builtins.print')
    def test_summarize_for_delegation_token_limit(self, mock_print, context_manager, large_history):
        """Test that delegation summary respects token limits."""
        task_description = "Analyze the conversation history"
        
        # Ensure the history ends with a user message
        if large_history[-1]["role"] != "user":
            large_history.append({"role": "user", "content": "Final user question"})
        
        # Set a very low token limit to force truncation
        max_tokens = 200
        summary = context_manager.summarize_for_delegation(
            large_history, task_description, max_tokens=max_tokens
        )
        
        # Check that summary is properly truncated
        estimated_tokens = context_manager.estimate_tokens(summary)
        assert estimated_tokens <= max_tokens
        
        # Check for truncation message
        assert "[Earlier history omitted to stay within context limits]" in summary
        
        # Verify essential content is included
        assert "# DELEGATED TASK" in summary
        assert task_description in summary
        assert "# CURRENT USER REQUEST" in summary
        assert large_history[-1]["content"] in summary
    
    def test_summarize_for_delegation_prioritization(self, context_manager, sample_history):
        """Test that summary prioritizes recent and important messages."""
        # Ensure we have a system prompt and the history ends with a user message
        if sample_history[0]["role"] != "system":
            sample_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})
            
        if sample_history[-1]["role"] != "user":
            sample_history.append({"role": "user", "content": "Final user question"})
            
        task_description = "This is a test task"
        
        with patch('builtins.print'):
            summary = context_manager.summarize_for_delegation(sample_history, task_description)
        
        # Most recent user message should be in CURRENT USER REQUEST section
        assert "# CURRENT USER REQUEST" in summary
        assert sample_history[-1]["content"] in summary
        
        # System message should be in SYSTEM PROMPT section
        assert "# SYSTEM PROMPT" in summary
        assert sample_history[0]["content"] in summary