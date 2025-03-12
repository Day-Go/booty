# Test Suite for LLM Project

This directory contains comprehensive tests for the hierarchical agent architecture in the LLM project. The tests focus on ensuring each component functions correctly both in isolation and as part of the integrated system.

## Overview

The test suite uses pytest and follows these testing principles:
- Unit tests for individual components
- Integration tests for component interactions
- Mocks and fixtures to isolate dependencies
- Comprehensive coverage of edge cases
- Consistency with the project's architecture

## Component Test Coverage

### XML Parser (`test_xml_parser.py`, `test_xml_parser_with_fixtures.py`, `test_xml_parser_integration.py`)
Tests the streaming XML parser that detects and extracts MCP commands from LLM output.

**Key Test Areas:**
- Identification of complete and partial XML commands
- Handling of nested tags, self-closing tags, and attributes with quotes
- Filtering out commands in think blocks
- Handling multiple commands in a single response
- Recovery from malformed XML
- Integration with streaming API responses

### Context Manager (planned: `test_context_manager.py`)
Will test the context management system that tracks token usage and helps prevent context overflow.

**Planned Test Areas:**
- Token estimation accuracy
- Context pruning strategies
- Context summarization for delegation
- Context usage warnings and monitoring

### Task Planner (planned: `test_task_planner.py`) 
Will test the component that analyzes requests and breaks them into discrete tasks.

**Planned Test Areas:**
- Request complexity analysis
- Task decomposition
- Task prioritization
- Delegation decisions

### Agent Management (planned: `test_transient_agent.py`, `test_agent_orchestrator.py`)
Will test the orchestrator and transient agent functionality.

**Planned Test Areas:**
- Agent initialization and configuration
- Task delegation between agents
- Result integration from multiple agents
- Error handling and recovery

### Filesystem Client (planned: `test_mcp_filesystem_client.py`)
Will test the client that manages file system operations.

**Planned Test Areas:**
- File reading and writing
- Directory listing and navigation
- Search and grep operations
- Security boundary enforcement

## Test Infrastructure

### Mocks and Test Utilities
- `mocks/terminal_utils.py` - Mock for terminal colors and formatting
- `mocks/simplified_parser.py` - Simplified parser implementation for reliable testing
- `xml_parser_for_testing.py` - Testing-specific version of the XML parser

### Test Fixtures
- `conftest.py` - Contains shared fixtures including sample MCP commands
- More fixtures will be added as needed for other components

## Running Tests

Run all tests:
```bash
python -m pytest
```

Run with verbose output:
```bash
python -m pytest -v
```

Run specific test modules or functions:
```bash
python -m pytest tests/test_xml_parser.py
python -m pytest tests/test_xml_parser.py::TestStreamingXMLParser::test_simple_mcp_command_detection
```

## Guidelines for Adding Tests

1. **Isolation**: Test one specific behavior per test function
2. **Dependencies**: Mock or fixture external dependencies
3. **Edge Cases**: Include tests for boundary and error conditions
4. **Naming**: Use descriptive test names that explain what's being tested
5. **Organization**: Group related tests in test classes
6. **Documentation**: Add docstrings explaining each test's purpose

As the project evolves, this test suite will expand to maintain comprehensive coverage of all components and their interactions.