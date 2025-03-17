"""
Ollama inference with hierarchical agent architecture.

This is the main entry point for the program. It sets up
multi-agent delegation for improved context management and task handling.
"""

import logging
import uvicorn
import threading
import time
import sys
import os
import requests
from requests.exceptions import ConnectionError

# Add src directory to path for relative imports when running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.terminal_utils import Colors
    from agents.agent_orchestrator import AgentOrchestrator
except ImportError:
    from src.utils.terminal_utils import Colors
    from src.agents.agent_orchestrator import AgentOrchestrator

# Default system prompt for the coding agent
with open("src/prompts/coding_agent_prompt.txt", "r") as f:
    CODING_AGENT_PROMPT = f.read()


def configure_uvicorn_logging():
    # Configure all uvicorn loggers to minimal output
    loggers = ["uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi", "fastapi"]

    # Create a null handler that discards all logs
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

    # Set all loggers to only show critical errors and route to null handler
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)
        logger.handlers = []
        logger.addHandler(NullHandler())
        logger.propagate = False


def start_mcp_filesystem_server():
    # Configure uvicorn logging before starting the server
    configure_uvicorn_logging()

    # Run the server with minimal logging settings
    uvicorn.run(
        "src.mcp.mcp_filesystem_server:app",
        host="127.0.0.1",
        port=8000,
        log_level="critical",
        access_log=False,
    )


def check_server_status(url, max_retries=15, retry_delay=0.5):
    """Check if the server is up and running by making a request to it."""
    for i in range(max_retries):
        try:
            response = requests.get(
                f"{url}/health"
            )  # Assuming there's a health endpoint
            if response.status_code == 200:
                return True
        except ConnectionError:
            print(f"Server not ready yet, retrying ({i + 1}/{max_retries})...")
        time.sleep(retry_delay)
    return False


# Example usage for hierarchical multi-agent coding assistant
if __name__ == "__main__":
    print(
        f"\n{Colors.BG_CYAN}{Colors.BOLD}Hierarchical Multi-Agent Coding Assistant{Colors.ENDC}"
    )
    print(
        f"{Colors.CYAN}This assistant can read files, search code, and help with programming tasks.{Colors.ENDC}"
    )
    print(f"{Colors.CYAN}Type 'exit' to quit.{Colors.ENDC}\n")

    # Setup configuration
    print(f"{Colors.BOLD}Setting up agent configuration...{Colors.ENDC}")
    model = "gemma3:27b"
    api_base = "http://localhost:11434"  # Ollama API endpoint
    mcp_fs_url = "http://127.0.0.1:8000"  # MCP Filesystem API endpoint
    max_agents = 10

    # Start mcp servers
    print(f"{Colors.BOLD}Starting MCP Filesystem server in background...{Colors.ENDC}")
    server_thread = threading.Thread(target=start_mcp_filesystem_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    if check_server_status(mcp_fs_url):
        print(f"{Colors.BOLD}MCP Filesystem server started successfully.{Colors.ENDC}")
    else:
        print(
            f"{Colors.BG_RED}{Colors.BOLD}Failed to start MCP Filesystem server.{Colors.ENDC}"
        )
        sys.exit(1)

    # Give the server a moment to start before continuing
    print(f"{Colors.BOLD}MCP Filesystem server started successfully.{Colors.ENDC}")

    # Create orchestrator with hierarchical agent architecture
    print(f"{Colors.BG_CYAN}{Colors.BOLD}Creating Agent Orchestrator{Colors.ENDC}")
    orchestrator = AgentOrchestrator(
        model=model,
        api_base=api_base,
        mcp_fs_url=mcp_fs_url,
        max_context_tokens=8192,
        system_prompt=CODING_AGENT_PROMPT,
        max_agents=max_agents,
    )

    print(f"{Colors.BG_GREEN}{Colors.BOLD}System initialized and ready{Colors.ENDC}")
    print(
        f"{Colors.GREEN}Available special commands: /status, /agents, /prune [n], /clear{Colors.ENDC}\n"
    )
    print(f"{Colors.CYAN}MCP filesystem server running on: {mcp_fs_url}{Colors.ENDC}")

    # Main interaction loop
    while True:
        print(f"\n{Colors.BOLD}User: {Colors.ENDC}", end="")
        user_input = input()

        # Check for exit command
        if user_input.lower() in ["exit", "quit", "q"]:
            print(
                f"\n{Colors.BG_CYAN}{Colors.BOLD}Exiting Hierarchical Multi-Agent Coding Assistant{Colors.ENDC}"
            )
            break

        # Skip empty input
        if not user_input.strip():
            continue

        # Process user input through the orchestrator
        try:
            print(f"{Colors.BG_CYAN}{Colors.BOLD}Processing request...{Colors.ENDC}")

            # The orchestrator handles delegating to transient agents or using the main agent
            response = orchestrator.chat(user_input, stream=True)

            # Add a separator after the response
            print(f"\n{Colors.CYAN}{'=' * 80}{Colors.ENDC}")

        except KeyboardInterrupt:
            print(
                f"\n{Colors.BG_YELLOW}{Colors.BOLD}Request interrupted by user{Colors.ENDC}"
            )
            continue

        except Exception as e:
            print(
                f"{Colors.BG_RED}{Colors.BOLD}Error processing request: {str(e)}{Colors.ENDC}"
            )
            print(f"{Colors.RED}Try again or type 'exit' to quit{Colors.ENDC}")
            continue
