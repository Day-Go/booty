"""
Ollama inference with hierarchical agent architecture.

This is the main entry point for the Ollama inference functionality with
multi-agent delegation for improved context management and task handling.
"""

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


# Example usage for hierarchical multi-agent coding assistant
if __name__ == "__main__":
    print(f"\n{Colors.BG_CYAN}{Colors.BOLD}Hierarchical Multi-Agent Coding Assistant{Colors.ENDC}")
    print(f"{Colors.CYAN}This assistant can read files, search code, and help with programming tasks.{Colors.ENDC}")
    print(f"{Colors.CYAN}Type 'exit' to quit.{Colors.ENDC}\n")

    # Setup configuration
    print(f"{Colors.BOLD}Setting up agent configuration...{Colors.ENDC}")
    model = "qwq:latest"  # Default Ollama model
    api_base = "http://localhost:11434"  # Ollama API endpoint
    mcp_fs_url = "http://127.0.0.1:8000"  # MCP Filesystem API endpoint
    max_agents = 3  # Maximum number of concurrent transient agents

    # Create orchestrator with hierarchical agent architecture
    orchestrator = AgentOrchestrator(
        model=model,
        api_base=api_base,
        mcp_fs_url=mcp_fs_url,
        max_context_tokens=32000,
        system_prompt=CODING_AGENT_PROMPT,
        max_agents=max_agents
    )

    print(f"{Colors.BG_GREEN}{Colors.BOLD}Orchestrator ready with {max_agents} max transient agents{Colors.ENDC}")
    print(f"{Colors.GREEN}Special commands: /status, /agents, /prune [n], /clear{Colors.ENDC}\n")

    # Main interaction loop
    while True:
        print(f"{Colors.BOLD}User: {Colors.ENDC}", end="")
        user_input = input()
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "q"]:
            print(f"\n{Colors.BG_CYAN}{Colors.BOLD}Exiting Hierarchical Multi-Agent Coding Assistant{Colors.ENDC}")
            break
        
        # Process user input through the orchestrator
        try:
            # The orchestrator handles delegating to transient agents or using the main agent
            response = orchestrator.chat(user_input, stream=True)
        except Exception as e:
            print(f"{Colors.BG_RED}{Colors.BOLD}Error: {str(e)}{Colors.ENDC}")
            continue