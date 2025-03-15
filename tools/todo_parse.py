#!/usr/bin/env python3
"""
Tool to parse Python files and extract TODO comments with priorities.

This script scans all Python files in the src and tests directories,
extracts comments with the format "# TODO: {comment} PRIORITY: {value}",
and generates a TODO.md file with references to file paths and line numbers.
"""

import os
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Define priority levels for sorting
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def find_project_root() -> str:
    """
    Find the project root directory by looking for src/ and tests/ directories.

    This works regardless of where the script is run from, even from a subdirectory.
    """
    # Start from the directory where the script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up directory levels until we find src/ and tests/ or hit the filesystem root
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        # Check if src/ or tests/ exist in this directory
        if os.path.exists(os.path.join(current_dir, "src")) or os.path.exists(
            os.path.join(current_dir, "tests")
        ):
            return current_dir

        # Go up one directory level
        current_dir = os.path.dirname(current_dir)

    # If we couldn't find a proper project root, use the current working directory
    # as a fallback with a warning
    cwd = os.getcwd()
    print(
        f"Warning: Could not find project root with src/ or tests/. Using current directory: {cwd}",
        file=sys.stderr,
    )
    return cwd


class TodoItem:
    """Represents a TODO item with its details."""

    def __init__(
        self,
        text: str,
        priority: str,
        file_path: str,
        line_number: int,
        completed: bool = False,
    ):
        self.text = text.strip()
        self.priority = priority.upper().strip()
        self.file_path = file_path
        self.line_number = line_number
        self.completed = completed

    def __str__(self) -> str:
        status = "[x]" if self.completed else ""
        return f"{status} {self.text} (PRIORITY: {self.priority})"

    def markdown_format(self) -> str:
        """Format the TODO item for markdown display."""
        checkbox = "- [ ]" if not self.completed else "- [x]"
        return f"{checkbox} {self.text} [{self.file_path}:{self.line_number}]"

    def matches_location(self, file_path: str, line_number: int) -> bool:
        """Check if this TODO matches the given file path and line number."""
        return self.file_path == file_path and self.line_number == line_number


def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                python_files.append(os.path.join(dirpath, filename))

    return python_files


def extract_todos(file_path: str) -> List[TodoItem]:
    """Extract TODO items with priorities from a file."""
    todos = []

    # Regular expression to match "# TODO: {text} PRIORITY: {priority}"
    todo_pattern = re.compile(r"#\s*TODO:\s*(.*?)\s*PRIORITY:\s*(\w+)", re.IGNORECASE)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                match = todo_pattern.search(line)
                if match:
                    todo_text = match.group(1).strip()
                    priority = match.group(2).strip()
                    todos.append(TodoItem(todo_text, priority, file_path, line_num))
    except Exception as e:
        print(f"Error processing file {file_path}: {e}", file=sys.stderr)

    return todos


def get_relative_path(file_path: str, base_dir: str) -> str:
    """Convert absolute path to path relative to the project root."""
    rel_path = os.path.relpath(file_path, base_dir)
    return rel_path


def parse_completed_todos(todo_file: str) -> List[Dict[str, Any]]:
    """
    Parse the TODO.md file to find completed items marked with [x].

    Returns:
        List of dictionaries with file path and line number of completed TODOs
    """
    completed_todos = []
    if not os.path.exists(todo_file):
        return completed_todos

    # Regular expression to match completed TODO items with file locations
    # Format: "- [x] Some todo text [file_path:line_number]"
    completed_pattern = re.compile(r"- \[x\] (.*?) \[(.*?):(\d+)\]")

    try:
        with open(todo_file, "r", encoding="utf-8") as file:
            for line in file:
                match = completed_pattern.search(line)
                if match:
                    text = match.group(1).strip()
                    file_path = match.group(2).strip()
                    line_number = int(match.group(3))

                    completed_todos.append(
                        {
                            "text": text,
                            "file_path": file_path,
                            "line_number": line_number,
                        }
                    )
    except Exception as e:
        print(f"Error parsing TODO.md for completed items: {e}", file=sys.stderr)

    return completed_todos


def remove_todo_from_file(file_path: str, line_number: int, project_root: str) -> bool:
    """
    Remove a TODO comment from a specific line in a file.

    Args:
        file_path: Relative path to the file
        line_number: Line number to remove the TODO from
        project_root: Project root directory

    Returns:
        True if successful, False otherwise
    """
    # Convert relative path to absolute
    abs_file_path = os.path.join(project_root, file_path)

    if not os.path.exists(abs_file_path):
        print(f"Error: File not found: {abs_file_path}", file=sys.stderr)
        return False

    try:
        # Read all lines from the file
        with open(abs_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Check if line number is valid
        if line_number <= 0 or line_number > len(lines):
            print(
                f"Error: Invalid line number {line_number} for file {file_path}",
                file=sys.stderr,
            )
            return False

        # Get the line to verify it contains a TODO
        line = lines[line_number - 1]
        if not re.search(r"#\s*TODO:", line, re.IGNORECASE):
            print(
                f"Warning: Line {line_number} in {file_path} does not contain a TODO comment",
                file=sys.stderr,
            )
            return False

        # Remove the line
        del lines[line_number - 1]

        # Write the updated content back to the file
        with open(abs_file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)

        print(f"Removed TODO from {file_path}:{line_number}")
        return True

    except Exception as e:
        print(
            f"Error removing TODO from {file_path}:{line_number}: {e}", file=sys.stderr
        )
        return False


def generate_markdown(
    todos: List[TodoItem], output_file: str, project_root: str
) -> None:
    """Generate a markdown file with the TODO items while preserving existing high-level TODOs."""
    # Read existing content if file exists
    existing_content = ""
    high_level_todos = ""
    completed_todos = []

    try:
        if os.path.exists(output_file):
            # Find completed TODOs before updating the file
            completed_todos = parse_completed_todos(output_file)

            # Process completed TODOs by removing them from source files
            for completed in completed_todos:
                remove_todo_from_file(
                    completed["file_path"], completed["line_number"], project_root
                )

            # Read the existing content
            with open(output_file, "r", encoding="utf-8") as existing_file:
                existing_content = existing_file.read()

            # Extract content before "### Scoped" section if it exists
            scoped_index = existing_content.find("### Scoped")
            if scoped_index != -1:
                high_level_todos = existing_content[:scoped_index].strip()
            else:
                high_level_todos = existing_content.strip()

    except Exception as e:
        print(f"Warning: Could not read existing TODO.md: {e}", file=sys.stderr)

    # Filter out todos that correspond to completed items
    filtered_todos = []
    for todo in todos:
        # Make file path relative to project root
        todo.file_path = get_relative_path(todo.file_path, project_root)

        # Check if this TODO corresponds to a completed item that was already removed
        is_completed = any(
            todo.file_path == completed["file_path"]
            and todo.line_number == completed["line_number"]
            for completed in completed_todos
        )

        if not is_completed:
            filtered_todos.append(todo)

    # Group TODOs by priority
    todos_by_priority = defaultdict(list)
    for todo in filtered_todos:
        todos_by_priority[todo.priority].append(todo)

    with open(output_file, "w", encoding="utf-8") as md_file:
        # Preserve high-level TODOs if they exist
        if high_level_todos:
            md_file.write(f"{high_level_todos}\n")
        else:
            md_file.write("# TODO List\n")
            md_file.write("[ ] Add high-level TODO items here\n")

        # Add scoped section with auto-generated TODOs
        md_file.write("\n### Scoped\n\n")

        # Define priorities to ensure a consistent order
        all_priorities = sorted(
            todos_by_priority.keys(), key=lambda p: PRIORITY_ORDER.get(p, 999)
        )

        if not all_priorities:
            md_file.write("No TODOs found in code comments.\n")
            return

        for priority in all_priorities:
            priority_todos = todos_by_priority[priority]
            md_file.write(f"#### {priority} Priority\n")

            if not priority_todos:
                md_file.write("No TODOs with this priority.\n")
                continue

            for todo in priority_todos:
                md_file.write(f"{todo.markdown_format()}\n")

            md_file.write("\n")


def main():
    """Main function to extract TODOs and generate markdown."""
    # Find project root directory (works even if script is in a subdirectory)
    project_root = find_project_root()

    # Define directories to scan
    src_dir = os.path.join(project_root, "src")
    tests_dir = os.path.join(project_root, "tests")

    # Verify directories exist
    if not os.path.exists(src_dir):
        print(f"Source directory not found: {src_dir}", file=sys.stderr)
        src_dir = None

    if not os.path.exists(tests_dir):
        print(f"Tests directory not found: {tests_dir}", file=sys.stderr)
        tests_dir = None

    # Output file path
    output_file = os.path.join(project_root, "TODO.md")

    # Check for completed TODOs first (before scanning files)
    # This is important because we want to remove completed TODOs from the source files
    # before we scan them again
    completed_count = 0
    if os.path.exists(output_file):
        completed_todos = parse_completed_todos(output_file)
        completed_count = len(completed_todos)
        if completed_count > 0:
            print(f"Found {completed_count} completed TODOs to remove")

    # Find all Python files
    python_files = []
    if src_dir:
        python_files.extend(find_python_files(src_dir))
    if tests_dir:
        python_files.extend(find_python_files(tests_dir))

    if not python_files:
        print("No Python files found to scan.", file=sys.stderr)
        return 1

    print(f"Found {len(python_files)} Python files to scan")

    # Extract TODOs from all files
    all_todos = []
    for file_path in python_files:
        file_todos = extract_todos(file_path)
        all_todos.extend(file_todos)

    # Generate markdown file, even if no TODOs were found
    # The generate_markdown function will handle both cases
    generate_markdown(all_todos, output_file, project_root)

    todo_count = len(all_todos) - completed_count  # Adjust for completed TODOs
    if completed_count > 0:
        print(f"Removed {completed_count} completed TODOs")
    print(f"Updated TODO.md with {todo_count} remaining code comment TODOs")

    return 0


if __name__ == "__main__":
    sys.exit(main())

