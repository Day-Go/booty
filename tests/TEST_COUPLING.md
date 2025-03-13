# Test-Source Coupling Guide

This document explains the mechanisms implemented to maintain coupling between tests and source code as the codebase evolves.

## The Problem

As codebases evolve, tests often become decoupled from the source code they're supposed to test. This leads to:

1. False positives: Tests pass but don't actually verify the current code
2. Broken tests: Code changes break tests in non-obvious ways
3. Missing test coverage: New features don't have corresponding tests

## Solution Components

We've implemented several mechanisms to maintain test-source coupling:

### 1. Contract Tests

Contract tests verify that mock implementations match their real counterparts. These tests are located in:

```
tests/e2e/mcp_filesystem/test_contract_coupling.py
```

They check that:
- Mock objects implement the same interface as real objects
- Command formats match between mock and real implementations

Run these tests after making changes to ensure mocks stay in sync:

```bash
pytest tests/e2e/mcp_filesystem/test_contract_coupling.py -v
```

### 2. Automated Test Updates

We've implemented tools to automatically update test code when source changes:

- `tools/update_mocks.py`: Updates mock implementations to match source
- `tools/watch_and_update.py`: Continuously watches source files and updates tests

Run the watcher during development:

```bash
python tools/watch_and_update.py
```

### 3. Pre-commit Checks

A pre-commit hook checks for test-source synchronization before allowing commits:

```bash
.git/hooks/pre-commit
```

It runs:
- Test-source synchronization checks
- Contract tests to verify compatibility

### 4. Test Dependency Annotations

Source files are annotated with their test dependencies:

```python
# Test dependencies:
# - tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py
# - tests/unit/xml_parser/test_xml_parser.py
```

Update these annotations with:

```bash
python tools/analyze_test_dependencies.py
```

### 5. Resilient Test Fixtures

We've implemented fixtures that make tests more resilient to API changes:

```python
from tests.e2e.mcp_filesystem.test_fixtures import resilient_e2e_test

@resilient_e2e_test()
def test_example():
    # Test code here
```

This decorator:
- Validates required components exist
- Patches filesystem API calls automatically
- Provides helpful error messages when APIs change

### 6. Test Synchronization Analysis

Run the synchronization check to find potential issues:

```bash
python tools/check_test_sync.py
```

It will report:
- Missing mock implementations
- Source files without tests
- API changes affecting tests

## Best Practices

1. **Run Contract Tests After Changes:**
   ```bash
   pytest tests/e2e/mcp_filesystem/test_contract_coupling.py -v
   ```

2. **Use the Resilient Test Decorator:**
   ```python
   @resilient_e2e_test()
   def test_function():
       # Test code here
   ```

3. **Update Test Dependencies:**
   ```bash
   python tools/analyze_test_dependencies.py
   ```

4. **Check Synchronization Before Committing:**
   ```bash
   python tools/check_test_sync.py
   ```

5. **Run the Test Update Watcher During Development:**
   ```bash
   python tools/watch_and_update.py
   ```

## Adding New Tests

When adding new tests:

1. Use the `resilient_e2e_test` decorator for end-to-end tests
2. Run `analyze_test_dependencies.py` to update source annotations
3. Verify contract compatibility with `test_contract_coupling.py`

## Adding New Source Files

When adding new source files:

1. Update `check_test_sync.py` to include the new file
2. Run `analyze_test_dependencies.py` to annotate the file
3. Add tests for the new file

## Troubleshooting

If you encounter test failures after source changes:

1. Run `python tools/update_mocks.py` to update mock implementations
2. Check for mismatches with `python tools/check_test_sync.py`
3. Review contract test failures for API compatibility issues

## Future Improvements

Potential improvements to the test-source coupling system:

1. Integration with CI/CD to block merges with decoupled tests
2. Mutation testing to verify test effectiveness
3. Automated test generation for new source files
4. Visualization of test-source dependencies