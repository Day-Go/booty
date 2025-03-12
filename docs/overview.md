Local LLM-Powered Coding Assistant Project

This project aims to create a command-line coding assistant that leverages local language models running on Ollama. The assistant will function similarly to Claude Code but will operate entirely locally for personal development use.

Key Specifications:
- Core implementation in Python 3
- Integration with Ollama for local model hosting and inference
- Command-line interface for developer interaction
- XML-based Model Control Protocol (MCP) for filesystem operations
- Specialized focus on Godot 4 game development
- Support for GDScript syntax highlighting and code completion
- Ability to understand and generate code that follows Godot 4's node-based architecture
- Knowledge of Godot 4's built-in classes, methods, and design patterns
- Capability to assist with both 2D and 3D game implementation
- Support for debugging common Godot-specific issues

## MCP Filesystem Interface

The project implements a robust Model Control Protocol (MCP) filesystem interface that uses XML-based syntax for commands. This approach provides several advantages:
- Structured command format using XML for reliable parsing
- Better handling of complex parameters and multi-line content
- Clearer organization of command components
- Reduced ambiguity in command detection and execution
- Extensibility for future command types

All filesystem operations are encapsulated in `<mcp:filesystem>` tags with individual commands specified as XML elements with appropriate attributes. See the `docs/mcp_filesystem.md` file for detailed documentation.

Example:
```xml
<mcp:filesystem>
    <read path="/path/to/file" />
    <list path="/path/to/directory" />
    <grep path="/path/to/search" pattern="search pattern" />
</mcp:filesystem>
```

The primary use case will be assisting in game development projects using the Godot 4 engine, including generating code snippets, explaining engine concepts, suggesting optimizations, and helping implement game mechanics following Godot best practices.