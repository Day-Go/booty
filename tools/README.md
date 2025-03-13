# Test-Source Coupling Tools

This directory contains tools for maintaining coupling between tests and source code.

## Available Tools

### check_test_sync.py

Verifies that tests are synchronized with source code:

```bash
python tools/check_test_sync.py
```

Features:
- Analyzes imports and dependencies in test files
- Verifies mock implementations match real implementations
- Reports any synchronization issues
- Returns non-zero exit code if tests are out of sync

### update_mocks.py

Automatically updates mock implementations based on current source code:

```bash
python tools/update_mocks.py
```

Features:
- Analyzes real implementations to extract interfaces
- Generates updated mock implementations
- Preserves custom behavior in updated mocks
- Updates mock imports if necessary

### watch_and_update.py

Watches for source code changes and updates tests automatically:

```bash
python tools/watch_and_update.py
```

Features:
- Watches source files for changes
- Triggers mock updates automatically
- Provides immediate feedback during development
- Reruns tests to verify changes

### analyze_test_dependencies.py

Analyzes and annotates test dependencies:

```bash
python tools/analyze_test_dependencies.py
```

Features:
- Parses imports and dependencies in test files
- Generates dependency maps for test-source relationships
- Annotates source files with dependent tests
- Creates reports of test coverage

## Pre-commit Hook

A pre-commit hook is provided in `/.git/hooks/pre-commit` that runs verification before allowing commits:

```bash
cp tools/pre-commit.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Usage

1. After making changes to source code, run:
   ```bash
   python tools/update_mocks.py
   ```

2. Verify synchronization:
   ```bash
   python tools/check_test_sync.py
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Commit changes (pre-commit hook will verify synchronization)

For detailed information on the test-source coupling framework, see:
- `/tests/TEST_COUPLING.md`: Comprehensive documentation
- `/docs/test_coupling.md`: Framework overview