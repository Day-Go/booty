import requests
import json
import os
import re
from typing import Dict, List, Any, Optional, Union


class MCPFilesystemClient:
    """Client for interacting with the MCP Filesystem Server"""
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
    
    def read_file(self, path: str) -> Dict[str, str]:
        """Read a file from the filesystem"""
        endpoint = f"{self.base_url}/read_file"
        payload = {"path": path}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        endpoint = f"{self.base_url}/write_file"
        payload = {"path": path, "content": content}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_directory(self, path: str) -> Dict[str, Any]:
        """List contents of a directory"""
        endpoint = f"{self.base_url}/list_directory"
        payload = {"path": path}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        endpoint = f"{self.base_url}/create_directory"
        payload = {"path": path}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_files(self, path: str, pattern: str) -> Dict[str, List[str]]:
        """Search for files matching pattern"""
        endpoint = f"{self.base_url}/search_files"
        payload = {"path": path, "pattern": pattern}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_allowed_directories(self) -> Dict[str, List[str]]:
        """Get list of allowed directories"""
        endpoint = f"{self.base_url}/list_allowed_directories"
        response = requests.get(endpoint)
        response.raise_for_status()
        return response.json()


class OfflineFileAgent:
    """Offline version of the agent that doesn't require Ollama API"""
    
    def __init__(self, mcp_fs_url="http://127.0.0.1:8000"):
        # Initialize MCP filesystem client
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)
        # Track tool usage
        self.tool_usage = []
    
    def _extract_file_commands(self, message: str) -> List[Dict[str, Any]]:
        """Extract file operation commands from a message"""
        commands = []
        
        # Match patterns for file operations
        read_pattern = r"read\s+file\s+(?:from\s+)?[\"']?([^\"']+)[\"']?"
        write_pattern = r"write\s+(?:to\s+)?file\s+[\"']?([^\"']+)[\"']?\s+with\s+content"
        list_pattern = r"list\s+(?:directory|dir|folder)\s+[\"']?([^\"']+)[\"']?"
        search_pattern = r"search\s+(?:for\s+)?[\"']?([^\"']+)[\"']?\s+in\s+[\"']?([^\"']+)[\"']?"
        
        # Extract read commands
        for match in re.finditer(read_pattern, message, re.IGNORECASE):
            path = match.group(1)
            commands.append({"action": "read", "path": path})
        
        # Extract write commands - note this is simplified, real impl would need to extract content too
        for match in re.finditer(write_pattern, message, re.IGNORECASE):
            path = match.group(1)
            commands.append({"action": "write", "path": path})
        
        # Extract list commands
        for match in re.finditer(list_pattern, message, re.IGNORECASE):
            path = match.group(1)
            commands.append({"action": "list", "path": path})
            
        # Extract search commands
        for match in re.finditer(search_pattern, message, re.IGNORECASE):
            pattern = match.group(1)
            path = match.group(2)
            commands.append({"action": "search", "path": path, "pattern": pattern})
            
        return commands

    def _execute_file_commands(self, commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute file operation commands using MCP Filesystem Server"""
        results = []
        
        for cmd in commands:
            action = cmd.get("action")
            path = cmd.get("path")
            
            try:
                if action == "read":
                    result = self.fs_client.read_file(path)
                    results.append({
                        "action": "read",
                        "path": path,
                        "success": True,
                        "content": result.get("content")
                    })
                    
                elif action == "list":
                    result = self.fs_client.list_directory(path)
                    results.append({
                        "action": "list",
                        "path": path,
                        "success": True,
                        "entries": result.get("entries")
                    })
                    
                elif action == "search":
                    pattern = cmd.get("pattern")
                    result = self.fs_client.search_files(path, pattern)
                    results.append({
                        "action": "search",
                        "path": path,
                        "pattern": pattern,
                        "success": True,
                        "matches": result.get("matches")
                    })
                    
                elif action == "write":
                    # Simplified, would normally get content from message
                    content = "This is test content written by Offline File Agent"
                    result = self.fs_client.write_file(path, content)
                    results.append({
                        "action": "write",
                        "path": path,
                        "success": result.get("success", False)
                    })
            except Exception as e:
                results.append({
                    "action": action,
                    "path": path,
                    "success": False,
                    "error": str(e)
                })
                
        return results

    def process_command(self, message: str) -> None:
        """Process a command from the user without LLM integration"""
        print(f"\nProcessing: {message}")
        
        # Process file commands in the message
        file_commands = self._extract_file_commands(message)
        
        if not file_commands:
            print("\nNo file commands detected. Try one of these formats:")
            print("- read file /path/to/file")
            print("- list directory /path/to/dir")
            print("- search for '*.py' in /path/to/dir")
            print("- write to file /path/to/file with content")
            return
        
        file_results = self._execute_file_commands(file_commands)
        self.tool_usage.extend(file_results)
        
        # Display results
        print("\nResults:")
        for result in file_results:
            action = result.get("action")
            path = result.get("path")
            success = result.get("success", False)
            
            print(f"\n[{action.upper()}] {path} - {'SUCCESS' if success else 'FAILED'}")
            
            if not success:
                print(f"Error: {result.get('error', 'Unknown error')}")
                continue
                
            if action == "read":
                content = result.get("content", "")
                if len(content) > 500:
                    print(f"Content (first 500 chars):\n{content[:500]}...\n(truncated)")
                else:
                    print(f"Content:\n{content}")
                    
            elif action == "list":
                entries = result.get("entries", [])
                print(f"Found {len(entries)} entries:")
                for entry in entries[:10]:  # Show first 10 entries
                    entry_type = entry.get("type", "unknown")
                    entry_size = entry.get("size", "")
                    size_str = f" ({entry_size} bytes)" if entry_size else ""
                    print(f"- {entry.get('name')} [{entry_type}{size_str}]")
                if len(entries) > 10:
                    print(f"... and {len(entries) - 10} more entries")
                    
            elif action == "search":
                pattern = result.get("pattern", "")
                matches = result.get("matches", [])
                print(f"Pattern '{pattern}' matched {len(matches)} files:")
                for match in matches[:10]:  # Show first 10 matches
                    print(f"- {match}")
                if len(matches) > 10:
                    print(f"... and {len(matches) - 10} more matches")


# Example usage for offline testing
if __name__ == "__main__":
    # Create an instance of OfflineFileAgent
    file_agent = OfflineFileAgent(mcp_fs_url="http://127.0.0.1:8000")

    # Interactive loop
    print("Offline File Agent initialized. Type 'exit' to quit.")
    print("Available commands:")
    print("  read file /path/to/file")
    print("  list directory /path/to/dir")
    print("  search for 'pattern' in /path/to/dir")
    print("  write to file /path/to/file with content")
    
    while True:
        user_input = input("\nCommand: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        
        file_agent.process_command(user_input)