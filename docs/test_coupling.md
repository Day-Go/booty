# Test-Source Coupling Framework

This document provides an overview of the test-source coupling framework implemented in this project.

## Purpose

The test-source coupling framework ensures that tests remain synchronized with the source code they verify as the codebase evolves. This prevents common issues such as:

- **False Positives**: Tests that pass but don't verify current code behavior
- **Broken Tests**: Tests that fail due to API changes rather than actual bugs
- **Missing Coverage**: Areas of code that lack proper test verification
- **Maintenance Overhead**: Manual effort required to keep tests in sync with code

## Components

The framework consists of several complementary mechanisms:

### 1. Contract Testing

Contract tests verify that mock implementations match real implementation interfaces:

- **Location**: `/tests/e2e/mcp_filesystem/test_contract_coupling.py`
- **Purpose**: Ensure mocks used in tests accurately reflect actual code behavior
- **Features**:
  - Verify method signatures (arguments, return types)
  - Verify core behavior for critical functionality
  - Detect API drift between mocks and real implementations

### 2. Automated Mock Updates

Tools that automatically update mock implementations when source code changes:

- **Location**: `/tools/update_mocks.py`
- **Purpose**: Reduce manual effort required to keep mocks synchronized with source
- **Features**:
  - Analyze real implementations to extract interfaces
  - Generate updated mock implementations
  - Preserve custom behavior in updated mocks

### 3. File Change Monitoring

Real-time detection of source code changes that might affect tests:

- **Location**: `/tools/watch_and_update.py`
- **Purpose**: Provide immediate feedback during development
- **Features**:
  - Watch source files for changes
  - Trigger mock updates automatically
  - Notify developers of potential test impacts

### 4. Test Dependency Analysis

AST-based analysis to identify which tests depend on which source files:

- **Location**: `/tools/analyze_test_dependencies.py`
- **Purpose**: Understand the impact of code changes on tests
- **Features**:
  - Parse imports and dependencies in test files
  - Generate dependency maps for test-source relationships
  - Annotate source files with dependent tests

### 5. Pre-commit Verification

Git hooks that prevent committing changes that break test-source coupling:

- **Location**: `/.git/hooks/pre-commit`
- **Purpose**: Enforce discipline in maintaining test-source coupling
- **Features**:
  - Run verification before allowing commits
  - Block commits that would break test-source coupling
  - Provide guidance on how to fix issues

### 6. Resilient Test Fixtures

Test fixtures that can adapt to minor API changes:

- **Location**: `/tests/e2e/mcp_filesystem/test_fixtures.py`
- **Purpose**: Make tests more robust against minor API changes
- **Features**:
  - Dynamically inspect real implementations
  - Adapt test parameters to match current implementations
  - Provide informative error messages when synchronization is needed

## Workflow

The recommended workflow for maintaining test-source coupling:

1. Make changes to source code
2. Run `python /tools/watch_and_update.py` to automatically update tests
3. Verify synchronization with `python /tools/check_test_sync.py`
4. Run tests with `pytest`
5. Commit changes (pre-commit hook will verify synchronization)

## Benefits

This framework provides several key benefits:

- **Reduced Maintenance**: Automated updates reduce manual effort
- **Early Detection**: Problems are caught during development, not in CI
- **Improved Reliability**: Tests accurately verify current code behavior
- **Better Understanding**: Developers understand test-source relationships
- **Enforced Discipline**: Pre-commit hooks prevent breaking the coupling

## Reference

For detailed information on specific components, refer to:

- `/tests/TEST_COUPLING.md`: Comprehensive documentation of all mechanisms
- `/tests/e2e/mcp_filesystem/test_contract_coupling.py`: Contract test examples
- `/tools/README.md`: Documentation for the coupling tools