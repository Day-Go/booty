# CLAUDE.md - Guidelines for LLM Project

## Commands
- Activate virtual environment: `source ~/pytorch-env/bin/activate`
- Check `TODO.md` for tasks to complete. Do not remove todo items from source manually, they are removed automatically with the next instruction.
- Mark in TODO.md tasks as complete once they are finished then run `python tools/todo_parse.py`
- Write changes in `CHANGES.md`. Make sure to reference the TODO item you were addressing. 
- Lint code: `flake8 src/ tests/`
- Type checking: `mypy --ignore-missing-imports src/ tests/`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/test_file.py::test_function -v`

## Code Style Guidelines
- Follow PEP 8 style guide with 4-space indentation
- Docstrings in triple quotes for functions/classes
- Use type hints consistently: `def function(param: type) -> return_type:`
- Imports order: standard library → third-party → local modules
- Error handling: use try/except blocks and raise_for_status() for API calls
- Class structure: clear __init__ methods, self-descriptive method names
- Variables: lowercase_with_underscores, CONSTANTS_ALL_CAPS
- Function arguments: positional first, then keyword with sensible defaults

## Project Organization
- src/ - Current implementation with Ollama integration
- docs/ - Project documentation
- tests/ - Test files (mirror src/ structure)
- requirements.txt - Python dependencies
