#!/usr/bin/env python3
"""
Tool to parse Python files and extract TODO comments with priorities.

This script scans all Python files in the src and tests directories,
extracts comments with the format "# TODO: {comment} PRIORITY: {value}",
and generates a TODO.md file with references to file paths and line numbers.
Supports both single-line and multiline TODO comments.
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
        end_line_number: Optional[int] = None,
    ):
        self.text = text.strip()
        self.priority = priority.upper().strip()
        self.file_path = file_path
        self.line_number = line_number
        self.end_line_number = end_line_number or line_number  # For multiline TODOs
        self.completed = completed

    def __str__(self) -> str:
        status = "[x]" if self.completed else ""
        return f"{status} {self.text} (PRIORITY: {self.priority})"

    def markdown_format(self) -> str:
        """Format the TODO item for markdown display."""
        checkbox = "- [ ]" if not self.completed else "- [x]"
        location = f"{self.file_path}:{self.line_number}"
        if self.end_line_number and self.end_line_number != self.line_number:
            location = f"{self.file_path}:{self.line_number}-{self.end_line_number}"
        return f"{checkbox} {self.text} [{location}]"

    def matches_location(self, file_path: str, line_number: int) -> bool:
        """Check if this TODO matches the given file path and line number."""
        # If it's a multiline TODO, consider it matched if the line_number is within its range
        if self.end_line_number and self.end_line_number != self.line_number:
            return (
                self.file_path == file_path
                and self.line_number <= line_number <= self.end_line_number
            )
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
    """Extract TODO items with priorities from a file, including multiline TODOs."""
    todos = []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # Read the entire file content
            file_content = file.read()

            # First find regular single-line TODOs
            # Regular expression to match "# TODO: {text} PRIORITY: {priority}"
            single_line_pattern = re.compile(
                r"^(.*?)#\s*TODO:\s*(.*?)\s*PRIORITY:\s*(\w+)(.*)$", re.MULTILINE
            )

            for match in single_line_pattern.finditer(file_content):
                # Get the line number by counting newlines before the match
                line_num = file_content[: match.start()].count("\n") + 1

                # Extract todo text and priority
                todo_text = match.group(2).strip()
                priority = match.group(3).strip()

                # If there's additional text after PRIORITY, it belongs to the todo
                if match.group(4):
                    additional_text = match.group(4).strip()
                    if additional_text:
                        todo_text += " " + additional_text

                todos.append(TodoItem(todo_text, priority, file_path, line_num))

            # Now find multiline TODOs
            # We'll look for patterns that begin with # TODO: and end with PRIORITY: {value}
            # with possibly multiple # comment lines in between
            multiline_pattern = re.compile(r"# TODO:(.*?)PRIORITY:\s*(\w+)", re.DOTALL)

            # Reread the file by lines for better line number tracking
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            # Reconstruct the file content with line numbers for processing
            line_indexed_content = ""
            for i, line in enumerate(lines):
                line_indexed_content += f"LINE{i + 1}:{line}"

            for match in multiline_pattern.finditer(file_content):
                # Extract the full text between TODO: and PRIORITY:
                full_text = match.group(1).strip()
                priority = match.group(2).strip()

                # Let's see if this is a true multiline TODO by checking for newlines
                if "\n" in full_text:
                    # Replace newlines followed by # with spaces to get a single line text
                    cleaned_text = re.sub(r"\n\s*#\s*", " ", full_text)

                    # Find the start line number
                    start_pos = file_content.find(match.group(0))
                    start_line = file_content[:start_pos].count("\n") + 1

                    # Find the end line number
                    end_pos = start_pos + len(match.group(0))
                    end_line = file_content[:end_pos].count("\n") + 1

                    # Check if we've already captured this as a single-line TODO
                    already_exists = any(
                        todo.line_number == start_line and todo.file_path == file_path
                        for todo in todos
                    )

                    if not already_exists:
                        todos.append(
                            TodoItem(
                                cleaned_text,
                                priority,
                                file_path,
                                start_line,
                                end_line_number=end_line,
                            )
                        )

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
    # Format: "- [x] Some todo text [file_path:line_number]" or "[file_path:line_number-end_line_number]"
    completed_pattern = re.compile(r"- \[x\] (.*?) \[(.*?):([\d-]+)\]")

    try:
        with open(todo_file, "r", encoding="utf-8") as file:
            for line in file:
                match = completed_pattern.search(line)
                if match:
                    text = match.group(1).strip()
                    file_path = match.group(2).strip()
                    line_info = match.group(3)

                    # Check if it's a multiline TODO (contains a range like 10-15)
                    if "-" in line_info:
                        start_line, end_line = map(int, line_info.split("-"))
                        completed_todos.append(
                            {
                                "text": text,
                                "file_path": file_path,
                                "line_number": start_line,
                                "end_line_number": end_line,
                            }
                        )
                    else:
                        # Single line TODO
                        line_number = int(line_info)
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


def remove_todo_from_file(
    file_path: str,
    line_number: int,
    project_root: str,
    end_line_number: Optional[int] = None,
) -> bool:
    """
    Remove a TODO comment from a specific line or range of lines in a file.

    Args:
        file_path: Relative path to the file
        line_number: Line number to remove the TODO from
        project_root: Project root directory
        end_line_number: End line number for multiline TODOs

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

        # If it's a multiline TODO
        if end_line_number and end_line_number != line_number:
            # Verify end_line_number is valid
            if end_line_number <= 0 or end_line_number > len(lines):
                print(
                    f"Error: Invalid end line number {end_line_number} for file {file_path}",
                    file=sys.stderr,
                )
                return False

            # Remove the range of lines
            del lines[line_number - 1 : end_line_number]
            print(
                f"Removed multiline TODO from {file_path}:{line_number}-{end_line_number}"
            )
        else:
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
            print(f"Removed TODO from {file_path}:{line_number}")

        # Write the updated content back to the file
        with open(abs_file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)

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
                end_line = completed.get("end_line_number")
                remove_todo_from_file(
                    completed["file_path"],
                    completed["line_number"],
                    project_root,
                    end_line,
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
            (
                todo.file_path == completed["file_path"]
                and todo.line_number == completed["line_number"]
                and (
                    not completed.get("end_line_number")
                    or todo.end_line_number == completed.get("end_line_number")
                )
            )
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
    generate_markdown(all_todos, output_file, project_root)

    todo_count = len(all_todos) - completed_count  # Adjust for completed TODOs
    if completed_count > 0:
        print(f"Removed {completed_count} completed TODOs")
    print(f"Updated TODO.md with {todo_count} remaining code comment TODOs")

    return 0


if __name__ == "__main__":
    sys.exit(main())

