# Context Manager Test Suite Documentation

This document provides an overview of the comprehensive test suite for the `ContextManager` class, which is responsible for tracking, estimating, and managing conversation context size in LLM applications.

## Test Structure

The context manager test suite consists of the following files:

1. **test_context_manager.py** - Basic functionality tests for core features
2. **test_context_manager_parametrized.py** - Parametrized tests for various inputs and scenarios
3. **test_context_manager_edge_cases.py** - Tests focused on boundary conditions and error handling
4. **test_context_manager_config.py** - Tests for different configuration options
5. **test_context_manager_integration.py** - Integration tests with realistic scenarios
6. **test_context_manager_performance.py** - Performance and stress tests (some skipped by default)

## Test Suites

### Basic Functionality Tests
These tests verify the core functionality of the context manager:
- Token estimation
- Context size checking
- Smart history pruning
- Delegation summarization

### Parametrized Tests
Tests that run the same test function with many different inputs:
- Various text lengths and character types
- Different token ratios
- Various history configurations
- Various pruning scenarios

### Edge Case Tests
Tests for handling unusual inputs and boundary conditions:
- Empty histories
- Malformed message structures
- Very large messages
- Non-ASCII/Unicode characters
- Negative or zero context windows
- Handling of error conditions

### Configuration Tests
Tests for different configuration options:
- Various context window sizes
- Different character-to-token ratios
- Model-specific behaviors

### Integration Tests
End-to-end scenarios that test how components work together:
- Realistic pruning scenarios
- Progressive context growth
- Delegation summarization with real data

### Performance Tests
Tests focused on performance and stress testing:
- Token estimation with large histories
- Pruning performance with large histories
- Multiple pruning cycles
- Mixed content types
- Repeated pruning stability

## Test Fixtures

The tests use several fixtures to provide test data:
- `context_manager` - Provides a fresh ContextManager instance
- `empty_history` - Provides an empty conversation history
- `sample_history` - Provides a typical conversation history
- `large_history` - Provides a history that exceeds context limits
- `unicode_history` - Provides history with Unicode characters
- `generate_large_history` - Generates history of specified size

## Running the Tests

To run all context manager tests:

```bash
python -m pytest tests/test_context_manager_*.py
```

To run a specific test file:

```bash
python -m pytest tests/test_context_manager_edge_cases.py
```

To run with verbose output:

```bash
python -m pytest tests/test_context_manager_*.py -v
```

## Skipped Tests

Some tests are skipped by default:
- Performance tests that would slow down the test suite
- Tests for features not yet implemented (persistence, custom thresholds)
- Tests that depend on specific implementation details

## Future Test Improvements

The test suite could be enhanced with:
1. More realistic token counting using a real LLM tokenizer
2. Property-based testing for more robust validation
3. Concurrent access tests for thread safety
4. Better isolation between tests
5. More diverse test data

## Implementation Notes

The context manager implementation provides these key functions:
- Estimating token usage in conversation history
- Warning when approaching context limits
- Smart pruning strategies:
  - Removing file operation results
  - Summarizing older messages
  - Removing oldest exchanges
- Preparing delegated contexts for transient agents

The test suite ensures all these functions work correctly across a wide variety of inputs and scenarios.