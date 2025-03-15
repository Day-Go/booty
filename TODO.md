- [ ] Add command line arg for launching agent in debug mode
- [ ] Implement testing framework where the agent executes the tests while running. Like a health check command /health initiats the routing and the agent tests mcp calls

### Scoped

#### CRITICAL Priority
- [ ] Remove pwd command and add new commands for changing directory and getting working directory. The commands are implemented in mcp_filesystem_server.py and mcp_filesystem_client.py. Documentation is in README_MCP_FILESYSTEM.md. [src/mcp_command_handler.py:102-105]

#### HIGH Priority
- [ ] This class is a mess. Hardcoded rules that aren't useful. Summarising the wikipedia page of a book would be considered a complex task Writing an advanced GPU algorithm would be considered trivial w/ no required planning This needs to be replaced with a lightweight model that decomposes tasks [src/task_planner.py:10-14]

#### MEDIUM Priority
- [ ] Replace hardcoded parameters with variables passed in from calling classes. [src/agent_orchestrator.py:58]

#### LOW Priority
- [ ] Extend behaviour to capture other sets of mcp commands, i.e. mcp:browser. [src/xml_parser.py:66]

