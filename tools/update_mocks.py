#!/usr/bin/env python3
"""
Script to automatically update mock implementations to match source code.

This tool helps maintain test-source coupling by:
1. Analyzing source code for interface changes
2. Updating mock implementations to match
3. Preserving custom logic while updating interfaces

Run this script after making changes to the source code to keep tests in sync.
"""

import os
import sys
import inspect
import importlib.util
import re
from typing import Dict, List, Any, Tuple, Optional, Set
import argparse
import ast

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


def load_module_from_path(path: str) -> Optional[Any]:
    """Load a Python module from a file path."""
    if not os.path.exists(path):
        return None
        
    try:
        module_name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module from {path}: {e}")
        return None


def get_class_methods(cls: Any) -> Dict[str, Any]:
    """Get all methods from a class."""
    return {
        name: obj for name, obj in inspect.getmembers(cls)
        if callable(obj) and not name.startswith('__')
    }


class MockUpdater:
    """Updates mock implementations to match their source counterparts."""
    
    def __init__(self, test_file_path: str, source_classes: Dict[str, Any],
                 mock_prefix: str = "Mock"):
        self.test_file_path = test_file_path
        self.source_classes = source_classes
        self.mock_prefix = mock_prefix
        self.test_file_content = ""
        
        # Load the test file content
        try:
            with open(test_file_path, 'r') as f:
                self.test_file_content = f.read()
        except Exception as e:
            print(f"Error reading test file: {e}")
    
    def generate_method_stub(self, method_name: str, method_obj: Any) -> str:
        """Generate a stub implementation for a method."""
        sig = inspect.signature(method_obj)
        params = []
        
        for name, param in sig.parameters.items():
            if name == 'self':
                params.append(name)
            elif param.default is inspect.Parameter.empty:
                params.append(name)
            else:
                params.append(f"{name}={repr(param.default)}")
        
        param_str = ", ".join(params)
        docstring = f'"""{method_obj.__doc__ or f"Mock implementation of {method_name}"}"""'
        
        return f"""
    def {method_name}({param_str}):
        {docstring}
        pass
"""
    
    def find_class_definition(self, class_name: str) -> Tuple[int, int, int]:
        """
        Find the start and end line of a class definition in the test file.
        
        Returns:
            Tuple of (start_line, end_line, indentation)
        """
        lines = self.test_file_content.split("\n")
        class_pattern = re.compile(rf"class\s+{class_name}\s*(?:\(.*?\))?:")
        
        start_line = -1
        indentation = 0
        
        # Find the class definition
        for i, line in enumerate(lines):
            if class_pattern.search(line):
                start_line = i
                indentation = len(line) - len(line.lstrip())
                break
        
        if start_line == -1:
            return (-1, -1, 0)
        
        # Find the end of the class
        end_line = start_line
        for i in range(start_line + 1, len(lines)):
            # Check if we're still in the class (more indented than class def)
            line_stripped = lines[i].lstrip()
            if not line_stripped:  # Skip empty lines
                end_line = i
                continue
                
            curr_indent = len(lines[i]) - len(line_stripped)
            if curr_indent <= indentation and line_stripped:
                # We've found a line that's less indented - end of class
                end_line = i - 1
                break
            
            end_line = i
        
        return (start_line, end_line, indentation)
    
    def add_missing_methods(self, mock_class_name: str, source_class_name: str) -> str:
        """
        Add missing methods to a mock class.
        
        Returns:
            Updated file content
        """
        source_class = self.source_classes.get(source_class_name)
        if not source_class:
            print(f"Error: Source class {source_class_name} not found")
            return self.test_file_content
        
        # Find the mock class in the test file
        start_line, end_line, indentation = self.find_class_definition(mock_class_name)
        if start_line == -1:
            print(f"Error: Mock class {mock_class_name} not found in test file")
            return self.test_file_content
        
        # Get source methods
        source_methods = get_class_methods(source_class)
        
        # Parse the test file to get existing methods
        try:
            tree = ast.parse(self.test_file_content)
        except Exception as e:
            print(f"Error parsing test file: {e}")
            return self.test_file_content
        
        # Find the mock class node
        mock_class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == mock_class_name:
                mock_class_node = node
                break
        
        if not mock_class_node:
            print(f"Error: Could not find mock class {mock_class_name} in AST")
            return self.test_file_content
        
        # Get existing methods
        existing_methods = set()
        for node in mock_class_node.body:
            if isinstance(node, ast.FunctionDef):
                existing_methods.add(node.name)
        
        # Find methods to add
        methods_to_add = []
        for method_name, method_obj in source_methods.items():
            if method_name not in existing_methods:
                methods_to_add.append((method_name, method_obj))
        
        if not methods_to_add:
            print(f"No missing methods to add to {mock_class_name}")
            return self.test_file_content
        
        # Generate method stubs and add them to the class
        lines = self.test_file_content.split("\n")
        new_lines = []
        
        # Add lines up to end of class
        for i in range(end_line + 1):
            new_lines.append(lines[i])
        
        # Check if we need to add a blank line
        if new_lines[-1].strip():
            new_lines.append("")
        
        # Add new methods
        for method_name, method_obj in methods_to_add:
            method_stub = self.generate_method_stub(method_name, method_obj)
            # Adjust indentation
            method_lines = method_stub.split("\n")
            for line in method_lines:
                if line.strip():
                    new_lines.append(" " * indentation + line)
                else:
                    new_lines.append("")
        
        # Add remaining lines
        for i in range(end_line + 1, len(lines)):
            new_lines.append(lines[i])
        
        print(f"Added {len(methods_to_add)} methods to {mock_class_name}")
        return "\n".join(new_lines)
    
    def update_all_mocks(self) -> str:
        """Update all mocks in the test file."""
        # Expected mock classes
        expected_mocks = {
            f"{self.mock_prefix}{class_name}": class_name
            for class_name in self.source_classes.keys()
        }
        
        updated_content = self.test_file_content
        
        # Update each mock
        for mock_name, source_name in expected_mocks.items():
            # Check if the mock class exists
            if f"class {mock_name}" in updated_content:
                updated_content = self.add_missing_methods(mock_name, source_name)
        
        return updated_content
    
    def save_updated_file(self, output_path: Optional[str] = None) -> bool:
        """Save the updated test file."""
        output_path = output_path or self.test_file_path
        updated_content = self.update_all_mocks()
        
        if updated_content == self.test_file_content:
            print("No changes needed to test file")
            return True
        
        try:
            with open(output_path, 'w') as f:
                f.write(updated_content)
            print(f"Successfully updated {output_path}")
            return True
        except Exception as e:
            print(f"Error writing updated test file: {e}")
            return False


def update_filesystem_mocks():
    """Update filesystem mocks to match source implementations."""
    # Import source classes
    try:
        from src.mcp_filesystem_client import MCPFilesystemClient
        from src.mcp_command_handler import MCPCommandHandler
        from src.xml_parser import StreamingXMLParser
        
        source_classes = {
            "MCPCommandHandler": MCPCommandHandler,
            "StreamingXMLParser": StreamingXMLParser,
            "MCPFilesystemClient": MCPFilesystemClient,
        }
    except ImportError as e:
        print(f"Error importing source classes: {e}")
        return False
    
    # Update test mocks
    test_file_path = os.path.join(project_root, "tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py")
    updater = MockUpdater(test_file_path, source_classes)
    return updater.save_updated_file()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update mock implementations to match source code")
    parser.add_argument("--check", action="store_true", help="Check only, don't update files")
    args = parser.parse_args()
    
    if args.check:
        # Check if updates are needed, but don't actually update
        # Implement this if needed
        print("Check mode not implemented yet")
        return
    
    # Update filesystem mocks
    update_filesystem_mocks()


if __name__ == "__main__":
    main()