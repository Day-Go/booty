# LLM Project Tests

This directory contains tests for the LLM project. The tests are organized into the following structure:

## Test Types

- **Unit Tests**: `/tests/unit/` - Tests for individual components
  - `context_manager/` - Tests for the context management system
  - `xml_parser/` - Tests for the XML parsing functionality

- **End-to-End Tests**: `/tests/e2e/` - Tests for full system functionality
  - `mcp_filesystem/` - E2E tests for the MCP filesystem functionality
    - `test_contract_coupling.py` - Contract tests for mock/real implementation compatibility
    - `test_helpers.py` - Helper functions for test-source coupling
    - `test_fixtures.py` - Test fixtures with resilient testing capabilities

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

## Test-Source Coupling Framework

This project implements a comprehensive test-source coupling framework to ensure tests remain synchronized with the source code they verify. For detailed information, see [TEST_COUPLING.md](/tests/TEST_COUPLING.md).

### Available Tools

- `/tools/check_test_sync.py` - Verifies test-source synchronization
- `/tools/update_mocks.py` - Automatically updates mock implementations
- `/tools/watch_and_update.py` - Watches for source changes and updates tests
- `/tools/analyze_test_dependencies.py` - Analyzes and annotates test dependencies

### Contract Testing

Contract tests in `/tests/e2e/mcp_filesystem/test_contract_coupling.py` verify that mock implementations match real implementation interfaces. These tests ensure that:

1. Mock method signatures match real implementations
2. Mock behavior matches real behavior for core functionality
3. Changes to source code are reflected in tests

### Resilient Testing

The `resilient_e2e_test` decorator in `/tests/e2e/mcp_filesystem/test_fixtures.py` makes tests more resilient to API changes by:

1. Dynamically inspecting real implementations
2. Adapting test parameters to match current implementations
3. Providing informative error messages when synchronization is needed

### Pre-commit Verification

A pre-commit hook in `/.git/hooks/pre-commit` prevents committing changes that would break test-source coupling by running the verification tools before allowing commits.

### Workflow

1. Make changes to source code
2. Run `python /tools/watch_and_update.py` to automatically update tests
3. Verify synchronization with `python /tools/check_test_sync.py`
4. Run tests with `pytest`
5. Commit changes (pre-commit hook will verify synchronization)