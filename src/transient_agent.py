"""Transient Agent for handling delegated tasks with clean context."""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import requests

from terminal_utils import Colors
from mcp_filesystem_client import MCPFilesystemClient
from xml_parser import StreamingXMLParser
from mcp_command_handler import MCPCommandHandler


class TransientAgent:
    """Lightweight agent for executing specific delegated tasks."""

    def __init__(
        self,
        task_id: str,
        task_description: str,
        model: str = "qwq:latest",
        api_base: str = "http://localhost:11434",
        mcp_fs_url: str = "http://127.0.0.1:8000",
        system_prompt: str = None,
    ):
        """Initialize a TransientAgent instance.

        Args:
            task_id: Unique identifier for the task
            task_description: Description of the delegated task
            model: Ollama model to use
            api_base: Ollama API base URL
            mcp_fs_url: MCP filesystem server URL
            system_prompt: Optional system prompt to guide the agent
        """
        self.task_id = task_id
        self.task_description = task_description
        self.model = model
        self.api_base = api_base
        self.agent_id = f"AGENT_{task_id}"

        # Initialize MCP command handler with this agent's ID
        self.mcp_handler = MCPCommandHandler(
            agent_id=self.agent_id, mcp_fs_url=mcp_fs_url
        )
        self.mcp_handler.set_debug_colors(Colors.GREEN, Colors.BG_GREEN)

        # For backward compatibility
        self.fs_client = MCPFilesystemClient(base_url=mcp_fs_url)

        self.system_prompt = system_prompt
        self.result = None
        self.status = "initialized"

        # Predefined system prompt if none provided
        if not self.system_prompt:
            self.system_prompt = (
                "You are a focused agent tasked with a specific job. "
                "Execute the task efficiently and return a concise summary of findings. "
                "Use available tools when needed. Do not add extraneous explanations."
            )

        print(
            f"{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Initialized for task: {task_description}{Colors.ENDC}"
        )

    def execute(self, context_summary: str, stream: bool = True) -> Dict[str, Any]:
        """Execute the delegated task and return results.

        Args:
            context_summary: Summarized context to provide task background
            stream: Whether to stream the response

        Returns:
            Dictionary with task results and metadata
        """
        self.status = "running"
        print(
            f"{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Executing task{Colors.ENDC}"
        )

        # Create prompt with task description and context
        prompt = (
            f"# TASK ASSIGNMENT\n{self.task_description}\n\n"
            f"# CONTEXT\n{context_summary}\n\n"
            f"Execute this task and provide a concise response. "
            f"Focus on giving exactly what was requested. "
            f"If you use any tools like file operations, include key findings but "
            f"summarize verbose outputs to keep your response compact."
        )

        # Generate response from Ollama
        try:
            print(
                f"{Colors.GREEN}[{self.agent_id}] Generating response for task{Colors.ENDC}"
            )

            # Get raw response with command execution
            response = self._generate_raw_response(prompt, self.system_prompt, stream)

            # Process the response to create a structured result
            result = self._process_response(response)

            self.result = result
            self.status = "completed"

            print(
                f"{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Task completed "
                f"successfully ({len(result['summary'])} chars summary){Colors.ENDC}"
            )

            return result

        except Exception as e:
            error_message = f"[{self.agent_id}] ERROR: {str(e)}"
            print(f"{Colors.BG_RED}{Colors.BOLD}{error_message}{Colors.ENDC}")

            self.result = {
                "task_id": self.task_id,
                "status": "failed",
                "error": str(e),
                "summary": f"Failed to complete task: {str(e)}",
                "raw_response": None,
            }
            self.status = "failed"

            return self.result

    def _process_response(self, response: str) -> Dict[str, Any]:
        """Process the raw response into a structured result.

        Args:
            response: The raw response from Ollama

        Returns:
            Structured result dictionary
        """
        # Extract any file operation results to store separately
        file_results = []

        # Look for file operation blocks with regex
        file_blocks = re.findall(
            r"---\s+(Content of|Contents of directory|Search results for|Grep results for)[^-]+---\s+(.*?)---",
            response,
            re.DOTALL,
        )

        # Store each file operation block
        for block_type, content in file_blocks:
            file_results.append({"type": block_type, "content": content.strip()})

        # Create a clean summary by removing file operation blocks
        summary = re.sub(
            r"---\s+(Content of|Contents of directory|Search results for|Grep results for)[^-]+---\s+.*?---",
            "",
            response,
            flags=re.DOTALL,
        )

        # Clean up any double newlines from removed blocks
        summary = re.sub(r"\n{3,}", "\n\n", summary)
        summary = summary.strip()

        # If summary is too long, create a more concise version
        if len(summary) > 1000:
            # Keep key findings section if it exists
            key_findings_match = re.search(
                r"(?:Key Findings|Summary|Results):(.*?)(?:\n\n|$)",
                summary,
                re.DOTALL | re.IGNORECASE,
            )

            if key_findings_match:
                concise_summary = f"Summary: {key_findings_match.group(1).strip()}"
            else:
                # Otherwise take the first paragraph and append a note
                first_para = summary.split("\n\n")[0].strip()
                concise_summary = f"{first_para}\n\n[Full response was {len(summary)} chars and has been summarized]"
        else:
            concise_summary = summary

        # Structure the result
        result = {
            "task_id": self.task_id,
            "status": "completed",
            "summary": concise_summary,
            "file_operations": file_results,
            "raw_response": response,
        }

        return result

    def _generate_raw_response(self, prompt, system_prompt=None, stream=True) -> str:
        """Generate a raw response from Ollama API with command detection.

        Args:
            prompt: The prompt to send to Ollama
            system_prompt: Optional system prompt
            stream: Whether to stream the response

        Returns:
            Raw response string
        """
        print(
            f"{Colors.BG_GREEN}{Colors.BOLD}[{self.agent_id}] Generating response{Colors.ENDC}"
        )

        endpoint = f"{self.api_base}/api/generate"

        # Build the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,  # Always stream for command detection
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make the request to Ollama API
        response = requests.post(endpoint, json=payload, stream=True)
        response.raise_for_status()

        # Process the streaming response and handle MCP commands
        return self.mcp_handler.process_streaming_response(
            response.iter_lines(),
            self.model,
            self.api_base,
            prompt,
            system_prompt,
            stream,
        )

