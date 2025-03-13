#!/usr/bin/env python3
"""
Script to check synchronization between tests and source code.

This tool helps prevent test-code desynchronization by:
1. Checking that mock implementations match real implementations 
2. Verifying tests exist for all source files
3. Detecting API changes that might break tests

Run this script as part of CI/CD or pre-commit hooks to catch synchronization issues early.
"""

import os
import sys
import inspect
import importlib.util
import re
from typing import Dict, List, Set, Any, Tuple, Optional
import argparse
import json

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


def get_public_methods(cls: Any) -> Set[str]:
    """Get all public method names from a class."""
    return {
        name for name, obj in inspect.getmembers(cls)
        if not name.startswith('_') and callable(obj)
    }


def find_source_files(root_dir: str, extensions: List[str] = None) -> List[str]:
    """Find all source files in a directory."""
    extensions = extensions or ['.py']
    source_files = []
    
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            # Check extensions
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(dirpath, filename)
                if not filepath.endswith('__init__.py'):
                    source_files.append(filepath)
                    
    return source_files


def check_mock_vs_real(mock_class: Any, real_class: Any) -> Tuple[Set[str], Set[str]]:
    """
    Check if a mock class implements the same interface as a real class.
    
    Returns:
        Tuple of (missing_essential, missing_other) methods
    """
    real_methods = get_public_methods(real_class)
    mock_methods = get_public_methods(mock_class)
    
    # Essential methods that should always be implemented
    essential_methods = {
        'MCPCommandHandler': {'extract_file_commands', 'execute_file_commands', 
                             'format_command_results', 'process_streaming_response'},
        'StreamingXMLParser': {'feed', 'get_command', 'reset'},
        'MCPFilesystemClient': {'read_file', 'write_file', 'list_directory', 'search_files'}
    }
    
    # Get the class name to determine which methods are essential
    class_name = real_class.__name__
    essential = essential_methods.get(class_name, set())
    
    # Check for missing methods
    missing_essential = essential - mock_methods
    missing_other = (real_methods - mock_methods) - essential
    
    return missing_essential, missing_other


def check_test_file_exists(source_path: str, test_dirs: List[str]) -> bool:
    """Check if a test file exists for a source file."""
    filename = os.path.basename(source_path)
    test_filename = f"test_{filename}"
    
    # Also check for class name pattern
    source_content = ""
    try:
        with open(source_path, 'r') as f:
            source_content = f.read()
    except Exception:
        pass
        
    # Extract class names for alternative test naming patterns
    class_names = []
    class_pattern = r"class\s+(\w+)\s*(?:\(.*?\))?:"
    class_matches = re.findall(class_pattern, source_content)
    if class_matches:
        class_names = class_matches
    
    # Check each test directory
    for test_dir in test_dirs:
        # Direct test file match
        if any(os.path.exists(os.path.join(root, test_filename)) 
               for root, _, _ in os.walk(test_dir)):
            return True
            
        # Check for class name pattern
        for class_name in class_names:
            class_test_pattern = f"test_{class_name.lower()}.py"
            if any(os.path.exists(os.path.join(root, class_test_pattern)) 
                   for root, _, _ in os.walk(test_dir)):
                return True
                
        # Check if any test file mentions the source file or its classes
        for test_root, _, test_files in os.walk(test_dir):
            for test_file in test_files:
                if not test_file.startswith("test_"):
                    continue
                    
                test_path = os.path.join(test_root, test_file)
                try:
                    with open(test_path, 'r') as f:
                        test_content = f.read()
                        
                    source_module = os.path.splitext(filename)[0]
                    # Check imports
                    if f"import {source_module}" in test_content or f"from {source_module}" in test_content:
                        return True
                        
                    # Check if any class is imported
                    for class_name in class_names:
                        if f"import {class_name}" in test_content or f"from .* import .*{class_name}" in test_content:
                            return True
                except Exception:
                    continue
                    
    return False


def check_filesystem_mocks():
    """Check synchronization of filesystem mocks."""
    # Load real implementations
    try:
        from src.mcp_filesystem_client import MCPFilesystemClient
        from src.mcp_command_handler import MCPCommandHandler
        from src.xml_parser import StreamingXMLParser
    except ImportError:
        print("Error: Could not import real implementations")
        return False
        
    # Load test mocks
    test_module_path = os.path.join(project_root, "tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py")
    test_module = load_module_from_path(test_module_path)
    
    if not test_module:
        print("Error: Could not load test module")
        return False
        
    # Get mock implementations
    mock_classes = {
        "MCPCommandHandler": getattr(test_module, "MockMCPCommandHandler", None),
        "StreamingXMLParser": getattr(test_module, "MockStreamingXMLParser", None)
    }
    
    # Check each mock
    all_synced = True
    for real_name, real_class in [
        ("MCPCommandHandler", MCPCommandHandler),
        ("StreamingXMLParser", StreamingXMLParser)
    ]:
        mock_class = mock_classes.get(real_name)
        if not mock_class:
            print(f"Error: No mock found for {real_name}")
            all_synced = False
            continue
            
        missing_essential, missing_other = check_mock_vs_real(mock_class, real_class)
        
        if missing_essential:
            print(f"Error: Mock {real_name} is missing essential methods: {missing_essential}")
            all_synced = False
            
        if missing_other:
            print(f"Warning: Mock {real_name} is missing non-essential methods: {missing_other}")
    
    # Check that essential source files have tests
    critical_sources = [
        "src/mcp_filesystem_client.py",
        "src/mcp_filesystem_server.py",
        "src/mcp_command_handler.py",
        "src/xml_parser.py"
    ]
    
    test_dirs = [
        os.path.join(project_root, "tests/e2e/mcp_filesystem"),
        os.path.join(project_root, "tests/unit/xml_parser")
    ]
    
    for source_path in critical_sources:
        full_path = os.path.join(project_root, source_path)
        if not os.path.exists(full_path):
            continue
            
        if not check_test_file_exists(full_path, test_dirs):
            print(f"Warning: No tests found for {source_path}")
            all_synced = False
    
    return all_synced


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check test-source synchronization")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings")
    args = parser.parse_args()
    
    # Check filesystem mocks
    success = check_filesystem_mocks()
    
    if not success and args.strict:
        sys.exit(1)
    elif not success:
        print("Warnings detected, but continuing")


if __name__ == "__main__":
    main()