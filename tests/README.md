# LLM Project Tests

This directory contains tests for the LLM project. The tests are organized into the following structure:

## Test Types

- **Unit Tests**: `/tests/unit/` - Tests for individual components
  - `context_manager/` - Tests for the context management system
  - `xml_parser/` - Tests for the XML parsing functionality

- **End-to-End Tests**: `/tests/e2e/` - Tests for full system functionality
  - `mcp_filesystem/` - E2E tests for the MCP filesystem functionality

## Running Tests

### All Tests

```bash
pytest
```

### Unit Tests Only

```bash
pytest tests/unit/
```

### E2E Tests Only

```bash
pytest tests/e2e/
```

### Specific Component Tests

```bash
pytest tests/unit/context_manager/
pytest tests/unit/xml_parser/
pytest tests/e2e/mcp_filesystem/
```

## E2E Test Environment

End-to-end tests require:

1. A running MCP filesystem server
2. Sample file structure for testing

The MCP filesystem tests include a mock project in `/tests/e2e/mcp_filesystem/mock_project/` which serves as a test environment.

## Test Fixtures

Common fixtures are defined in:

- `/tests/conftest.py` - Global fixtures
- `/tests/unit/context_manager/conftest.py` - Context manager fixtures
- `/tests/e2e/mcp_filesystem/conftest.py` - MCP filesystem fixtures

## Adding New Tests

1. Create tests in the appropriate directory
2. Name test files with `test_` prefix
3. Name test functions with `test_` prefix
4. Use fixtures from the corresponding conftest.py file