"""
Ollama inference with MCP filesystem integration.

This is the main entry point for the Ollama inference functionality.
It uses refactored modules for each component following the single responsibility principle.
"""

from terminal_utils import Colors
from ollama_agent import OllamaAgent


# Example usage for a coding agent with MCP filesystem integration
if __name__ == "__main__":
    # Define the system prompt with detailed file command instructions
    system_prompt = """You are an expert coding assistant with filesystem access capabilities.

To access files or directories, use XML-formatted commands within <mcp:filesystem> tags. Here's how to use them:

<mcp:filesystem>
    <read path="/path/to/file" />
    <write path="/path/to/file">Content to write to the file</write>
    <list path="/path/to/directory" />
    <search path="/path/to/search" pattern="search pattern" />
    <pwd />
    <grep path="/path/to/search" pattern="grep pattern" />
</mcp:filesystem>

CRITICAL REQUIREMENTS FOR COMMANDS:
- Commands MUST be wrapped in <mcp:filesystem> tags
- Each command is an XML element with appropriate attributes
- File paths MUST start with / (absolute paths only)
- Use proper XML syntax - each tag must be properly closed
- For write commands, place the content between opening and closing tags
- Pattern attributes must be enclosed in quotes
- These commands will be detected and executed in real-time as you generate them
- DO NOT hallucinate or invent the output of these commands

COMMAND EXECUTION WORKFLOW:
1. When you issue an MCP filesystem command, your generation will be immediately interrupted
2. The command will be executed and the results will be shown
3. You will then continue your response incorporating the command results
4. You can use multiple commands throughout your response as needed

ANTI-HALLUCINATION GUIDELINES:
- You have NO knowledge of file contents until you read them with commands
- You have NO knowledge of directory structures until you list them
- If you feel compelled to guess what's in a file, issue a command to read it instead
- If you don't know what's in a directory, issue a list command first

EXAMPLE OF CORRECT USAGE:
"I'll start by determining the current working directory to establish our absolute base path:

<mcp:filesystem>
    <pwd />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now that I know we're working in /home/user/project, I'll check the main implementation file and project structure:

<mcp:filesystem>
    <read path="/home/user/project/main.py" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"I see this is a Flask application. Let me look at the directory structure:

<mcp:filesystem>
    <list path="/home/user/project" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now I'll examine the model implementation files:

<mcp:filesystem>
    <read path="/home/user/project/models/user.py" />
</mcp:filesystem>"

[YOUR GENERATION IS INTERRUPTED, COMMAND IS EXECUTED, AND RESULTS ARE SHOWN]

"Now I understand how the components work together. According to the files I've read, the system uses SQLAlchemy for database access..."
"""

    # Create an OllamaAgent with system prompt directly initialized
    coding_agent = OllamaAgent(
        model="qwq:latest",
        mcp_fs_url="http://127.0.0.1:8000",
        max_context_tokens=32000,  # QwQ model context size
        system_prompt=system_prompt,  # Initialize with system prompt
    )

    # Interactive loop
    print("Coding Agent with File System Access initialized. Type 'exit' to quit.")
    print(
        "\nIMPORTANT: File commands are now detected and executed in real-time using XML syntax."
    )
    print("The AI uses these formats within <mcp:filesystem> tags:")
    print('  <read path="/path/to/file" />')
    print('  <list path="/path/to/dir" />')
    print('  <search path="/path/to/dir" pattern="search pattern" />')
    print('  <write path="/path/to/file">Content goes here</write>')
    print("  <pwd />")
    print('  <grep path="/path/to/dir" pattern="grep pattern" />')

    print("\nIMPORTANT WORKFLOW:")
    print("1. When the AI uses a command, generation is immediately interrupted")
    print("2. The system executes the command and shows REAL results")
    print("3. The AI then continues its response incorporating the results")
    print("4. This prevents hallucination as the AI only works with real data")
    print("5. The AI can use multiple commands throughout its response")

    print("\nNEW FEATURES:")
    print("1. Real-time XML command detection and execution")
    print("2. Streaming token analysis for immediate command processing")
    print("3. Seamless interruption and continuation of model generation")
    print("4. Better handling of complex multi-line content")
    print("5. Context management: Use these commands to manage conversation context:")
    print("   - /status - Show current context size and usage")
    print("   - /prune [n] - Remove older messages, keeping last n exchanges")
    print("   - /clear - Clear all conversation history")
    print("\nExample questions you can ask:")
    print('- "Can you analyze how ollama_inference.py works?"')
    print('- "What\'s in the project structure and how does it all connect?"')
    print('- "Find all Python files related to Ollama integration"')
    print('- "Explain the file system operations in this project"')
    print()
    print("The AI will retrieve the necessary files and provide a thorough analysis.")
    print(
        "If context gets too large, the system will warn you and provide options to manage it."
    )
    print()

    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        # No need to pass system_prompt each time - it's stored in the agent
        response = coding_agent.chat(user_input, stream=True)