import pytest
import time
import sys
import os
import random
import string

# Add the src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tests.context_manager_for_testing import ContextManager


@pytest.fixture
def context_manager():
    """Fixture to provide a fresh ContextManager instance for each test."""
    return ContextManager(max_context_tokens=4000, token_ratio=4)


@pytest.fixture
def generate_large_history(size=100):
    """Fixture to generate a large conversation history with specified number of messages."""
    def _generate(size):
        history = []
        roles = ["user", "assistant"]
        
        for i in range(size):
            # Random content length between 50-500 characters
            content_length = random.randint(50, 500)
            content = ''.join(random.choice(string.ascii_letters + string.digits + ' ') 
                              for _ in range(content_length))
            
            history.append({
                "role": roles[i % 2],
                "content": content
            })
        
        return history
    
    return _generate


def test_token_estimation_performance(context_manager, generate_large_history):
    """Test the performance of token estimation with large histories."""
    # Skip this test in regular test runs
    pytest.skip("Performance test - run only when performance profiling is needed")
    
    for size in [10, 100, 1000]:
        history = generate_large_history(size)
        
        # Measure time for token estimation
        start_time = time.time()
        tokens = context_manager.estimate_tokens(history)
        end_time = time.time()
        
        elapsed = end_time - start_time
        print(f"Token estimation for {size} messages took {elapsed:.4f} seconds")
        
        # Acceptable performance criteria would depend on specific requirements
        # Here's a simple assertion that might need adjustment
        assert elapsed < size * 0.01, f"Token estimation too slow for {size} messages"


def test_pruning_performance(context_manager, generate_large_history):
    """Test the performance of history pruning with large histories."""
    # Skip this test in regular test runs
    pytest.skip("Performance test - run only when performance profiling is needed")
    
    for size in [10, 100, 1000]:
        history = generate_large_history(size)
        
        # Measure time for pruning
        start_time = time.time()
        pruned_history = context_manager.smart_prune_history(history)
        end_time = time.time()
        
        elapsed = end_time - start_time
        print(f"History pruning for {size} messages took {elapsed:.4f} seconds")
        
        # Assertions about performance
        assert elapsed < size * 0.05, f"Pruning too slow for {size} messages"
        assert len(pruned_history) <= len(history), "Pruning should not increase history size"


def test_multiple_pruning_cycles(context_manager, generate_large_history):
    """Test the effectiveness of multiple pruning cycles."""
    history = generate_large_history(50)
    
    # Track token counts through multiple pruning cycles
    token_counts = []
    
    # Initial token count
    tokens = context_manager.estimate_tokens(history)
    token_counts.append(tokens)
    
    # Perform multiple pruning cycles
    for _ in range(3):
        history = context_manager.smart_prune_history(history)
        tokens = context_manager.estimate_tokens(history)
        token_counts.append(tokens)
    
    # Each pruning cycle should reduce tokens
    for i in range(1, len(token_counts)):
        assert token_counts[i] <= token_counts[i-1], "Pruning should reduce token count"
    
    # The final token count should be significantly lower than the initial
    assert token_counts[-1] < token_counts[0] * 0.8, "Multiple pruning cycles should significantly reduce tokens"


def test_stress_with_mixed_content(context_manager):
    """Test with a mix of normal messages, file operations, code blocks, and very long messages."""
    # Create a stress test history with various content types
    history = []
    
    # Add some normal messages
    for i in range(5):
        history.append({"role": "user", "content": f"Normal message {i}"})
        history.append({"role": "assistant", "content": f"Normal response {i}"})
    
    # Add messages with file operations
    for i in range(3):
        history.append({"role": "user", "content": f"Please read file {i}"})
        history.append({"role": "assistant", "content": f"Here's the file content:\n```\nFile content for file {i}\nMore content...\n```"})
    
    # Add messages with code blocks
    for i in range(2):
        history.append({"role": "user", "content": f"Write code for task {i}"})
        history.append({"role": "assistant", "content": f"Here's the code:\n```python\ndef function_{i}():\n    return 'Hello world'\n```"})
    
    # Add one very long message
    history.append({"role": "user", "content": "A" * 2000})
    history.append({"role": "assistant", "content": "B" * 2000})
    
    # Test token estimation using check_context_size
    status_tuple = context_manager.check_context_size(history)
    tokens = status_tuple[1]  # Extract tokens from the tuple
    assert tokens > 0
    
    # Check status is returned as a tuple now
    assert isinstance(status_tuple, tuple)
    assert len(status_tuple) == 3  # (status, tokens, percentage)
    
    pruned_history = context_manager.smart_prune_history(history)
    assert len(pruned_history) <= len(history)
    
    # Check if the context size improved after pruning
    pruned_tokens = context_manager.estimate_tokens(pruned_history)
    assert pruned_tokens < tokens


def test_repeated_pruning_stability(context_manager, generate_large_history):
    """Test that repeated pruning converges to a stable state."""
    history = generate_large_history(30)
    
    # Apply pruning multiple times
    prev_size = len(history)
    pruned_history = history
    
    for _ in range(5):
        pruned_history = context_manager.smart_prune_history(pruned_history)
        current_size = len(pruned_history)
        
        # Eventually, pruning should stabilize
        # Either no change or smaller each time
        assert current_size <= prev_size
        
        prev_size = current_size
        
        # If no change in last round, we've reached stable state
        if current_size == prev_size and _ > 0:
            break
    
    # Ensure summarization for delegation works with the pruned history
    summary = context_manager.summarize_for_delegation(pruned_history, "Test task for delegation")
    assert summary != ""