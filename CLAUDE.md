# CLAUDE.md - Guidelines for LLM Project

## Commands
- Activate virtual environment: `source ~/pytorch-env/bin/activate`
- Run Ollama inference: `python src/ollama_inference.py`
- Run legacy QwQ model: `python legacy/run_qwq_4bit.py`
- Lint code: `flake8 src/ legacy/ tests/`
- Type checking: `mypy --ignore-missing-imports src/ legacy/ tests/`
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
- legacy/ - Original QwQ model implementation
- docs/ - Project documentation
- tests/ - Test files (mirror src/ structure)
- requirements.txt - Python dependencies
