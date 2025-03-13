#!/usr/bin/env python3
"""
Script to analyze and annotate source files with their test dependencies.

This tool helps maintain test-source coupling by:
1. Analyzing which tests depend on which source files
2. Annotating source files with their test dependencies
3. Providing a way to quickly find tests affected by source changes

Example annotation added to source files:
```python
# Test dependencies:
# - tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py
# - tests/unit/xml_parser/test_xml_parser.py
```
"""

import os
import sys
import ast
import re
import argparse
from typing import Dict, List, Set, Any, Optional

# Add project root to path to ensure imports work
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


class ImportCollector(ast.NodeVisitor):
    """AST visitor to collect import statements in a Python file."""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = {}
        
    def visit_Import(self, node):
        for name in node.names:
            self.imports.add(name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module
            if module not in self.from_imports:
                self.from_imports[module] = set()
            for name in node.names:
                self.from_imports[module].add(name.name)
        self.generic_visit(node)


def find_source_files(root_dir: str) -> List[str]:
    """Find all Python source files in a directory."""
    source_files = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py") and not filename.startswith("_"):
                filepath = os.path.join(dirpath, filename)
                source_files.append(filepath)
                    
    return source_files


def find_test_files(root_dir: str) -> List[str]:
    """Find all test files in a directory."""
    test_files = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith("test_") and filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                test_files.append(filepath)
                    
    return test_files


def analyze_test_file(test_file: str) -> Dict[str, Set[str]]:
    """
    Analyze a test file to determine which source files it imports.
    
    Returns:
        Dict mapping source module to imported symbols
    """
    with open(test_file, "r") as f:
        content = f.read()
        
    # Parse the file
    try:
        tree = ast.parse(content)
    except Exception as e:
        print(f"Error parsing {test_file}: {e}")
        return {}
        
    # Collect imports
    collector = ImportCollector()
    collector.visit(tree)
    
    # Process imports
    direct_imports = collector.imports
    from_imports = collector.from_imports
    
    result = {}
    
    # Map imports to source files
    for module in direct_imports:
        # Check if this is a project module
        if module.startswith("src."):
            source_module = module
            result[source_module] = {"*"}
        
    # Map from imports to source files
    for module, names in from_imports.items():
        # Check if this is a project module
        if module.startswith("src."):
            source_module = module
            result[source_module] = names
            
    return result


def find_dependencies(test_files: List[str]) -> Dict[str, Set[str]]:
    """
    Find which test files depend on which source files.
    
    Returns:
        Dict mapping source module to test files
    """
    # Map from source module to test files
    dependencies = {}
    
    for test_file in test_files:
        # Analyze the test file
        imports = analyze_test_file(test_file)
        
        # Update dependencies
        for source_module, _ in imports.items():
            if source_module not in dependencies:
                dependencies[source_module] = set()
            dependencies[source_module].add(test_file)
    
    return dependencies


def module_to_filepath(module: str) -> str:
    """Convert a module name to a file path."""
    return os.path.join(project_root, module.replace(".", "/") + ".py")


def annotate_source_file(file_path: str, test_files: Set[str], dry_run: bool = False) -> bool:
    """
    Annotate a source file with its test dependencies.
    
    Args:
        file_path: Path to the source file
        test_files: Set of test files that depend on this source file
        dry_run: Whether to actually modify the file
        
    Returns:
        Whether the file was modified
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    with open(file_path, "r") as f:
        content = f.read()
    
    # Remove existing test dependency comments
    content = re.sub(r"# Test dependencies:.*?(?=\n\S|\Z)", "", content, flags=re.DOTALL)
    
    # Create new annotation
    if test_files:
        # Make paths relative to project root
        rel_test_files = [os.path.relpath(test_file, project_root) for test_file in test_files]
        rel_test_files.sort()
        
        annotation = "# Test dependencies:\n"
        for test_file in rel_test_files:
            annotation += f"# - {test_file}\n"
        
        # Add annotation after imports
        try:
            tree = ast.parse(content)
            
            # Find the last import statement
            last_import_lineno = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_lineno = max(last_import_lineno, node.lineno)
            
            # Add annotation after imports or at the beginning
            if last_import_lineno > 0:
                lines = content.split("\n")
                while last_import_lineno < len(lines) and (not lines[last_import_lineno].strip() or lines[last_import_lineno].startswith("#")):
                    last_import_lineno += 1
                
                new_content = "\n".join(lines[:last_import_lineno])
                new_content += "\n\n" + annotation + "\n"
                new_content += "\n".join(lines[last_import_lineno:])
            else:
                # Add at the beginning, after doc comment if present
                if content.startswith('"""') or content.startswith("'''"):
                    end_doc = content.find('"""', 3)
                    if end_doc == -1:
                        end_doc = content.find("'''", 3)
                    
                    if end_doc != -1:
                        end_doc += 3
                        new_content = content[:end_doc] + "\n\n" + annotation + content[end_doc:]
                    else:
                        new_content = annotation + "\n" + content
                else:
                    new_content = annotation + "\n" + content
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            # Fall back to adding at the beginning
            new_content = annotation + "\n" + content
    else:
        # No dependencies, just remove the annotation
        new_content = content
    
    # Check if the file was actually modified
    if new_content == content:
        return False
        
    # Write the modified file
    if not dry_run:
        with open(file_path, "w") as f:
            f.write(new_content)
            
    return True


def analyze_and_annotate():
    """Analyze test dependencies and annotate source files."""
    # Find all test files
    test_files = find_test_files(os.path.join(project_root, "tests"))
    print(f"Found {len(test_files)} test files")
    
    # Find dependencies
    print("Analyzing test dependencies...")
    dependencies = find_dependencies(test_files)
    
    # Get reverse mapping from source file to test files
    source_to_tests = {}
    for module, tests in dependencies.items():
        file_path = module_to_filepath(module)
        if os.path.exists(file_path):
            if file_path not in source_to_tests:
                source_to_tests[file_path] = set()
            source_to_tests[file_path].update(tests)
    
    # Annotate source files
    print(f"Found {len(source_to_tests)} source files with test dependencies")
    for source_file, tests in source_to_tests.items():
        print(f"Annotating {os.path.basename(source_file)} with {len(tests)} test dependencies")
        annotate_source_file(source_file, tests)
    
    print("Done!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze and annotate source files with test dependencies")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify files")
    args = parser.parse_args()
    
    analyze_and_annotate()


if __name__ == "__main__":
    main()