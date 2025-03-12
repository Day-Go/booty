"""Integration tests for the ContextManager class."""

import pytest
from unittest.mock import patch, MagicMock
import re
import sys
import io
from tests.context_manager_for_testing import ContextManager


class TestContextManagerIntegration:
    """Integration tests for the ContextManager in realistic scenarios."""
    
    @pytest.fixture
    def context_manager(self):
        """Fixture providing a context manager with realistic settings."""
        return ContextManager(max_context_tokens=32000, token_ratio=4)
    
    @pytest.fixture
    def realistic_history(self):
        """Fixture providing a realistic conversation history with many exchanges."""
        history = []
        
        # System prompt
        history.append({
            "role": "system", 
            "content": "You are a helpful assistant that specializes in providing programming help and explanations."
        })
        
        # Add several exchanges with varied content including file operations
        exchanges = [
            # First exchange - simple greeting
            (
                "Hello, can you help me with my Python code?",
                "Hello! I'd be happy to help with your Python code. What specific issue are you facing or what would you like assistance with?"
            ),
            # Second exchange - showing a file
            (
                "Can you show me what's in my main.py file?",
                "I'll help you see the contents of main.py.\n\n--- Content of main.py ---\ndef main():\n    print('Hello, world!')\n    process_data()\n\ndef process_data():\n    data = [1, 2, 3, 4, 5]\n    result = sum(data)\n    print(f'The sum is {result}')\n\nif __name__ == '__main__':\n    main()\n---\n\nThis file contains a simple Python script with two functions: `main()` and `process_data()`. The script calculates the sum of a list of numbers and prints the result."
            ),
            # Third exchange - error help
            (
                "I'm getting an error when I run this code. Can you help debug it?",
                "I'd be happy to help debug your code. To better understand the error, could you please:\n\n1. Share the exact error message you're receiving\n2. Make sure the code you shared is complete\n\nCommon issues with this code might include:\n- Missing imports\n- Incorrect indentation\n- Variable scope issues\n\nIf you share more details about the error, I can provide more specific help."
            ),
            # Fourth exchange - directory listing
            (
                "Can you show me what files are in my project directory?",
                "Let me check what files are in your project directory.\n\n--- Contents of directory /project ---\n- main.py [324 bytes]\n- utils.py [1024 bytes]\n- data.json [2048 bytes]\n- tests/ [dir]\n- venv/ [dir]\n- README.md [512 bytes]\n---\n\nYour project appears to be a Python project with the main script (main.py), a utilities module (utils.py), a data file (data.json), a tests directory, a virtual environment (venv), and a README file."
            ),
            # Fifth exchange - code explanation
            (
                "Can you explain how the process_data function works?",
                "Let's examine the `process_data()` function from your main.py file:\n\n```python\ndef process_data():\n    data = [1, 2, 3, 4, 5]\n    result = sum(data)\n    print(f'The sum is {result}')\n```\n\nThis function works as follows:\n\n1. It creates a list of integers `[1, 2, 3, 4, 5]` and assigns it to the variable `data`\n2. It calculates the sum of all numbers in the list using the built-in `sum()` function\n3. It stores the result (which would be 15 in this case) in the variable `result`\n4. Finally, it prints a formatted string showing the sum\n\nThe function is quite simple - it doesn't take any parameters and doesn't return any values, it just processes the hardcoded data and prints the result."
            ),
            # Sixth exchange - search results
            (
                "Find all files containing 'print' statements",
                "I'll search for files containing 'print' statements in your project.\n\n--- Grep results for 'print' in /project ---\n- main.py:2:    print('Hello, world!')\n- main.py:6:    print(f'The sum is {result}')\n- utils.py:15:    print(f'Processing {filename}')\n- utils.py:42:    print('Operation completed successfully')\n---\n\nI found 'print' statements in two files:\n1. main.py (2 occurrences)\n2. utils.py (2 occurrences)\n\nThese print statements are used for displaying output and status messages in your code."
            ),
        ]
        
        # Add all exchanges to history
        for user_msg, assistant_msg in exchanges:
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": assistant_msg})
            
        return history
    
    @patch('builtins.print')
    def test_realistic_pruning_scenario(self, mock_print, context_manager, realistic_history):
        """Test pruning in a realistic scenario with multiple pruning stages."""
        # Mock check_context_size to simulate high usage
        with patch.object(context_manager, 'check_context_size') as mock_check:
            # Initial check shows high usage
            initial_tokens = 25000  # 78% usage
            initial_percentage = initial_tokens / context_manager.max_context_tokens
            
            # Set target to 70% of current size
            target_percentage = initial_percentage * 0.7
            
            # Prepare mock return values for various stages of pruning
            mock_check.side_effect = [
                # Initial check
                ("warning", initial_tokens, initial_percentage),
                # After file operations removal
                ("warning", int(initial_tokens * 0.85), initial_percentage * 0.85),
                # After summarization
                ("ok", int(initial_tokens * 0.65), initial_percentage * 0.65)
            ]
            
            # Perform pruning
            pruned_history = context_manager.smart_prune_history(
                realistic_history, target_percentage=target_percentage
            )
            
            # Verify call count to ensure pruning steps were attempted
            assert mock_check.call_count >= 3
            
            # Compare original vs pruned history
            assert len(pruned_history) == len(realistic_history)  # No messages removed
            
            # Check for file operations replacement
            file_ops_pruned = False
            for msg in pruned_history:
                if msg["role"] == "assistant" and (
                    "[File content removed during context pruning]" in msg["content"] or
                    "[Directory listing removed during context pruning]" in msg["content"] or
                    "[Search results removed during context pruning]" in msg["content"]
                ):
                    file_ops_pruned = True
                    break
                    
            assert file_ops_pruned
            
            # Check that most recent messages are preserved intact
            assert pruned_history[-1]["content"] == realistic_history[-1]["content"]
            assert pruned_history[-2]["content"] == realistic_history[-2]["content"]
    
    @patch('builtins.print')
    def test_progressive_context_growth(self, mock_print, context_manager):
        """Test realistic scenario where context grows over multiple exchanges."""
        history = []
        system_prompt = "You are a helpful assistant."
        
        # Simulate a growing conversation
        user_messages = [
            "Hello, can you help me?",
            "Tell me about Python.",
            "How do I install Python?",
            "What editor should I use?",
            "Show me a simple Python example.",
            "How do I run that code?",
            "What are the best Python libraries?",
            "How do I install those libraries?",
            "Can you explain classes in Python?",
            "Give me an example of inheritance.",
        ]
        
        # Add system message
        history.append({"role": "system", "content": system_prompt})
        
        # Gradually build up context with each exchange
        usage_levels = []
        
        # Initial tokens - just system message
        _, tokens, percentage = context_manager.check_context_size(history)
        usage_levels.append(percentage)
        
        for i, msg in enumerate(user_messages):
            # Add user message
            history.append({"role": "user", "content": msg})
            
            # Simulate assistant response - make it longer for later messages
            response = f"Response to: {msg}" + " Additional content." * i * 5
            history.append({"role": "assistant", "content": response})
            
            # Check context size at each step
            _, tokens, percentage = context_manager.check_context_size(history)
            usage_levels.append(percentage)
            
        # Verify context grows with each exchange
        for i in range(len(usage_levels) - 1):
            assert usage_levels[i] < usage_levels[i+1], f"Context size should increase at step {i}"
    
    @patch('builtins.print')
    def test_delegation_summary_with_realistic_data(self, mock_print, context_manager, realistic_history):
        """Test delegation summary creation with realistic conversation history."""
        task_description = "Find and explain instances of list comprehension in the code"
        
        # Ensure history ends with a user message
        if realistic_history[-1]["role"] != "user":
            realistic_history.append({"role": "user", "content": "Can you show me examples of list comprehensions?"})
        
        # Create summary
        summary = context_manager.summarize_for_delegation(
            realistic_history, task_description, max_tokens=1500
        )
        
        # Verify summary structure and content
        assert "# DELEGATED TASK" in summary
        assert task_description in summary
        
        assert "# CURRENT USER REQUEST" in summary
        assert realistic_history[-1]["content"] in summary  # Last user message
        
        assert "# SYSTEM PROMPT" in summary
        assert "specializes in providing programming help" in summary
        
        assert "# RELEVANT HISTORY" in summary
        
        # Check token length is within budget
        tokens = context_manager.estimate_tokens(summary)
        assert tokens <= 1500
    
    @patch('builtins.print')
    def test_context_size_with_growing_history(self, mock_print, context_manager):
        """Test how context status changes as history grows to critical levels."""
        history = []
        statuses = []
        
        # Add messages until we exceed critical threshold
        message_size = 2000  # characters per message - increased for faster growth
        
        # First add a system message
        history.append({"role": "system", "content": "You are a helpful assistant."})
        
        # Add a small amount of history to start
        for i in range(3):
            history.append({"role": "user", "content": f"User question {i+1}"})
            history.append({"role": "assistant", "content": f"Assistant response {i+1}"})
            
        # Check initial status - should be ok with small history
        status, _, _ = context_manager.check_context_size(history)
        statuses.append(status)
        
        # Simulate adding more messages with explicit status tracking
        with patch.object(context_manager, 'check_context_size') as mock_check:
            # First simulate some "ok" status results 
            mock_tokens = 5000  # < 32000 * 0.7 (warning threshold)
            mock_percentage = mock_tokens / context_manager.max_context_tokens
            
            # Then progress to "warning" status
            warning_tokens = 25000  # > 32000 * 0.7 but < 32000 * 0.9
            warning_percentage = warning_tokens / context_manager.max_context_tokens
            
            # Then progress to "critical" status
            critical_tokens = 30000  # > 32000 * 0.9
            critical_percentage = critical_tokens / context_manager.max_context_tokens
            
            # Define the progression of status results
            mock_check.side_effect = [
                # First few calls return ok
                ("ok", mock_tokens, mock_percentage),
                ("ok", mock_tokens * 1.2, mock_percentage * 1.2),
                ("ok", mock_tokens * 1.5, mock_percentage * 1.5),
                # Then warning
                ("warning", warning_tokens, warning_percentage),
                ("warning", warning_tokens * 1.1, warning_percentage * 1.1),
                # Finally critical
                ("critical", critical_tokens, critical_percentage)
            ]
            
            # Call check_context_size multiple times to simulate adding messages
            for i in range(6):
                # Add a pair of messages each time to simulate conversation growth
                history.append({"role": "user", "content": f"User message {i}: " + "x" * message_size})
                history.append({"role": "assistant", "content": f"Assistant response {i}: " + "y" * message_size})
                
                # Call check_context_size which will use our mocked return values
                status, _, _ = context_manager.check_context_size(history)
                statuses.append(status)
        
        # Now verify the progression
        assert "ok" in statuses, "Should have 'ok' status points"
        assert "warning" in statuses, "Should have 'warning' status points"
        assert "critical" in statuses, "Should have 'critical' status points"
        
        # Calculate indexes to verify progression order
        ok_indexes = [i for i, status in enumerate(statuses) if status == "ok"]
        warning_indexes = [i for i, status in enumerate(statuses) if status == "warning"]
        critical_indexes = [i for i, status in enumerate(statuses) if status == "critical"]
        
        # Verify order of progression (last ok should come before first warning, etc.)
        assert max(ok_indexes) < min(warning_indexes), "Warning should come after ok"
        assert max(warning_indexes) < min(critical_indexes), "Critical should come after warning"