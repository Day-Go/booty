#!/usr/bin/env python3
"""
Script to watch source files and automatically update tests when changes are detected.

This tool helps maintain test-source coupling by:
1. Monitoring source files for changes
2. Automatically updating test mocks when source files change
3. Running tests to verify changes don't break existing tests

Run this script in a separate terminal while developing to keep tests in sync.
"""

import os
import sys
import time
import subprocess
import argparse
from typing import List, Set, Dict, Any, Optional
import importlib.util
import hashlib

# Add project root to path to ensure imports work
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


def get_file_hash(file_path: str) -> str:
    """Get a hash of a file's contents."""
    if not os.path.exists(file_path):
        return ""
        
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def watch_files(files_to_watch: List[str], 
               test_files: List[str], 
               update_script: str, 
               poll_interval: float = 1.0):
    """
    Watch source files and update tests when changes are detected.
    
    Args:
        files_to_watch: List of source files to watch
        test_files: List of test files to update and run
        update_script: Path to script that updates test files
        poll_interval: How often to check for changes (in seconds)
    """
    # Track file hashes to detect changes
    file_hashes = {file_path: get_file_hash(file_path) for file_path in files_to_watch}
    
    print(f"Watching {len(files_to_watch)} files for changes...")
    print(f"Will update {len(test_files)} test files when changes are detected")
    
    try:
        while True:
            # Check for changes
            changes_detected = False
            changed_files = []
            
            for file_path in files_to_watch:
                current_hash = get_file_hash(file_path)
                if current_hash != file_hashes[file_path]:
                    changes_detected = True
                    changed_files.append(file_path)
                    file_hashes[file_path] = current_hash
            
            if changes_detected:
                print(f"\nChanges detected in {len(changed_files)} files:")
                for file_path in changed_files:
                    print(f"  - {os.path.basename(file_path)}")
                
                # Run the update script
                print("\nUpdating test files...")
                try:
                    subprocess.run(["python", update_script], check=True)
                    print("Test files updated successfully")
                except subprocess.CalledProcessError as e:
                    print(f"Error updating test files: {e}")
                
                # Run the tests to verify everything still works
                print("\nRunning tests...")
                try:
                    for test_file in test_files:
                        print(f"Running {os.path.basename(test_file)}...")
                        subprocess.run(["python", "-m", "pytest", test_file, "-v"], check=False)
                except subprocess.CalledProcessError as e:
                    print(f"Error running tests: {e}")
                
                print("\nAll done. Continuing to watch for changes...")
            
            # Wait for next check
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print("\nStopping file watcher")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Watch source files and update tests when changes are detected")
    parser.add_argument("--interval", type=float, default=1.0, help="Poll interval in seconds")
    parser.add_argument("--update-script", type=str, default="tools/update_mocks.py", help="Script to run when changes are detected")
    args = parser.parse_args()
    
    # Files to watch
    source_files = [
        os.path.join(project_root, "src/mcp_filesystem_client.py"),
        os.path.join(project_root, "src/mcp_filesystem_server.py"),
        os.path.join(project_root, "src/mcp_command_handler.py"),
        os.path.join(project_root, "src/xml_parser.py"),
    ]
    
    # Test files to update and run
    test_files = [
        os.path.join(project_root, "tests/e2e/mcp_filesystem/test_contract_coupling.py"),
        os.path.join(project_root, "tests/e2e/mcp_filesystem/test_mcp_filesystem_e2e.py"),
    ]
    
    # Start watching
    watch_files(source_files, test_files, args.update_script, args.interval)


if __name__ == "__main__":
    main()