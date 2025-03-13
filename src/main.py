"""
Ollama inference with hierarchical agent architecture.

This is the main entry point for the Ollama inference functionality with
multi-agent delegation for improved context management and task handling.
"""

import io
import sys
import logging
import uvicorn
import threading
import time
from terminal_utils import Colors
from agent_orchestrator import AgentOrchestrator


# Default system prompt for the coding agent
CODING_AGENT_PROMPT = """You are a coding assistant that can help with software development tasks.
You have access to the filesystem to read code, search for files, and help users understand
and modify their codebase. Use XML-formatted MCP commands to interact with files when needed.

Example MCP commands:
<mcp:filesystem>
  <pwd />
</mcp:filesystem>

<mcp:filesystem>
  <read path="/path/to/file.py" />
</mcp:filesystem>

<mcp:filesystem>
  <list path="/path/to/directory" />
</mcp:filesystem>

<mcp:filesystem>
  <grep path="/path/to/directory" pattern="search_pattern" />
</mcp:filesystem>

<mcp:filesystem>
  <search path="/path/to/directory" pattern="*.py" />
</mcp:filesystem>

<mcp:filesystem>
  <write path="/path/to/new_file.py">
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
  </write>
</mcp:filesystem>
"""


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
        "mcp_filesystem_server:app",
        host="127.0.0.1",
        port=8000,
        log_level="critical",
        access_log=False,
    )


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
    max_agents = 10  # Maximum number of concurrent transient agents

    # Start mcp servers
    print(f"{Colors.BOLD}Starting MCP Filesystem server in background...{Colors.ENDC}")
    server_thread = threading.Thread(target=start_mcp_filesystem_server, daemon=True)
    server_thread.start()

    # Give the server a moment to start before continuing
    time.sleep(1)
    print(f"{Colors.BOLD}MCP Filesystem server started successfully.{Colors.ENDC}")

    # Create orchestrator with hierarchical agent architecture
    print(f"{Colors.BG_CYAN}{Colors.BOLD}Creating Agent Orchestrator{Colors.ENDC}")
    orchestrator = AgentOrchestrator(
        model=model,
        api_base=api_base,
        mcp_fs_url=mcp_fs_url,
        max_context_tokens=32000,
        system_prompt=CODING_AGENT_PROMPT,
        max_agents=max_agents,
    )

    print(
        f"{Colors.BG_GREEN}{Colors.BOLD}System initialized and ready{Colors.ENDC}"
    )
    print(
        f"{Colors.GREEN}Available special commands: /status, /agents, /prune [n], /clear{Colors.ENDC}\n"
    )
    print(
        f"{Colors.CYAN}MCP filesystem server running on: {mcp_fs_url}{Colors.ENDC}"
    )

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
            print(f"\n{Colors.CYAN}{'='*80}{Colors.ENDC}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.BG_YELLOW}{Colors.BOLD}Request interrupted by user{Colors.ENDC}")
            continue
            
        except Exception as e:
            print(f"{Colors.BG_RED}{Colors.BOLD}Error processing request: {str(e)}{Colors.ENDC}")
            print(f"{Colors.RED}Try again or type 'exit' to quit{Colors.ENDC}")
            continue

