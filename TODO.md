- [ ] Add command line arg for launching agent in debug mode

### Scoped

#### CRITICAL Priority
- [ ] The contents of this folder is out of date and no longer reflects how the filesystem mcp commands are formatter, and how the server/clients are implemented. We need to review this file and make sure it matches the implementation in mcp_filesystem_client.py, mcp_filysystem_server.py, mcp_command_handler and README_MCP_FILESYSTEM.md. [src/ollama_inference_offline.py:7-12]

#### HIGH Priority
- [ ] This class is a mess. Hardcoded rules that aren't useful. Summarising the wikipedia page of a book would be considered a complex task Writing an advanced GPU algorithm would be considered trivial w/ no required planning This needs to be replaced with a lightweight model that decomposes tasks [src/task_planner.py:10-14]

#### MEDIUM Priority
- [ ] Replace hardcoded parameters with variables passed in from calling classes. [src/agent_orchestrator.py:58]

#### LOW Priority
- [ ] Extend behaviour to capture other sets of mcp commands, i.e. mcp:browser. [src/xml_parser.py:66]

