"""Agent Orchestrator for managing hierarchical agent structure."""

from typing import Dict, List, Any, Optional, Union, Tuple
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

try:
    from utils.terminal_utils import Colors
    from agents.task_planner import TaskPlanner
    from utils.context_manager import ContextManager
    from agents.transient_agent import TransientAgent
    from agents.ollama_agent import OllamaAgent
except ImportError:
    from src.utils.terminal_utils import Colors
    from src.agents.task_planner import TaskPlanner
    from src.utils.context_manager import ContextManager
    from src.agents.transient_agent import TransientAgent
    from src.agents.ollama_agent import OllamaAgent


class AgentOrchestrator:
    """Orchestrates the interaction between main and transient agents."""

    def __init__(
        self,
        model: str = "qwq:latest",
        api_base: str = "http://localhost:11434",
        mcp_fs_url: str = "http://127.0.0.1:8000",
        max_context_tokens: int = 32000,
        system_prompt: str = None,
        max_agents: int = 3,
    ):
        """Initialize the Agent Orchestrator.

        Args:
            model: Ollama model to use
            api_base: Ollama API base URL
            mcp_fs_url: MCP filesystem server URL
            max_context_tokens: Maximum token context for the model
            system_prompt: Optional system prompt
            max_agents: Maximum number of concurrent transient agents
        """
        # Configuration
        self.model = model
        self.api_base = api_base
        self.mcp_fs_url = mcp_fs_url
        self.max_agents = max_agents

        # Default system prompts
        self.main_agent_prompt = system_prompt or (
            "You are an assistant with advanced capabilities who can use tools to help accomplish user tasks. "
            "You have access to file operations and can coordinate with specialized agents to handle complex tasks. "
            "Break down complex problems and delegate when appropriate."
        )

        self.transient_agent_prompt = (
            "You are a focused agent tasked with a specific job. "
            "Execute your assigned task efficiently and return a concise summary of findings. "
            "Avoid unnecessary explanations and focus on delivering exactly what was requested."
        )

        print(f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Initializing{Colors.ENDC}")

        # Initialize the main agent with multi-model orchestration for context summarization
        # TODO: Replace hardcoded parameters with variables passed in from calling classes. PRIORITY: MEDIUM
        self.main_agent = OllamaAgent(
            model=model,
            api_base=api_base,
            mcp_fs_url=mcp_fs_url,
            max_context_tokens=max_context_tokens,
            system_prompt=self.main_agent_prompt,
            agent_id="MAIN_AGENT",
            summarizer_model="gemma3:12b",
            summarizer_max_tokens=32000,
            enable_context_summarization=True,
            tokenizer_name="cl100k_base",
        )

        # Initialize support components
        self.task_planner = TaskPlanner()
        self.context_manager = ContextManager(max_context_tokens=max_context_tokens)

        # Transient agent management
        self.active_agents = {}  # task_id -> agent
        self.transient_results = {}  # task_id -> result

        # Thread management
        self.executor = ThreadPoolExecutor(max_workers=max_agents)
        self.result_queue = Queue()

        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Initialized with "
            f"{max_context_tokens} max tokens and {max_agents} max concurrent agents{Colors.ENDC}"
        )

    def chat(self, message: str, system_prompt: str = None, stream: bool = True) -> str:
        """Main chat interface for the orchestrator.

        This is the primary entry point for user interactions:
        1. Analyzes the user request
        2. Creates a task plan if needed
        3. Delegates complex subtasks to transient agents
        4. Coordinates all responses into a coherent result

        Args:
            message: User message
            system_prompt: Optional system prompt
            stream: Whether to stream response

        Returns:
            Generated response
        """
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Processing chat request{Colors.ENDC}"
        )
        # Handle special commands
        if message.lower().startswith("/"):
            return self._handle_special_command(message)

        # Analyze request for task planning
        request_analysis = self.task_planner.analyze_request(message)

        # If simple request, just pass to main agent
        if not request_analysis["requires_planning"]:
            print(
                f"{Colors.BLUE}[ORCHESTRATOR] Simple request detected, using main agent directly{Colors.ENDC}"
            )
            print(
                f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Activated{Colors.ENDC}"
            )
            response = self.main_agent.chat(message, system_prompt, stream)
            print(f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Complete{Colors.ENDC}")
            return response

        # For complex requests, create a task plan
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Complex request detected, creating task plan{Colors.ENDC}"
        )
        task_plan = self.task_planner.create_task_plan(message, request_analysis)

        # Check context size before proceeding
        context_status, _, usage = self.context_manager.check_context_size(
            self.main_agent.conversation_history, self.main_agent.system_prompt
        )

        # Prune context if too large
        if context_status == "critical":
            print(
                f"{Colors.BG_RED}{Colors.BOLD}[ORCHESTRATOR] Context critically large, pruning history{Colors.ENDC}"
            )
            self.main_agent.conversation_history = (
                self.context_manager.smart_prune_history(
                    self.main_agent.conversation_history, target_percentage=0.7
                )
            )

        # Check if we have tasks for delegation
        delegatable_tasks = [
            t for t in task_plan["tasks"] if t["delegate_to_transient"]
        ]

        if not delegatable_tasks:
            print(
                f"{Colors.BLUE}[ORCHESTRATOR] No delegatable tasks, using main agent{Colors.ENDC}"
            )
            # Just use main agent if no tasks to delegate
            print(
                f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Activated{Colors.ENDC}"
            )
            response = self.main_agent.chat(message, system_prompt, stream)
            print(f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Complete{Colors.ENDC}")
            return response

        # Begin delegation process
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Starting delegation of {len(delegatable_tasks)} tasks{Colors.ENDC}"
        )

        # Preserve original request for main agent
        self.main_agent.conversation_history.append(
            {"role": "user", "content": message}
        )

        # Delegate tasks to transient agents
        task_results = self._delegate_tasks(delegatable_tasks, message)

        # Format results for main agent
        delegation_summary = self._format_delegation_results(task_results)

        # Update the prompt for the main agent with delegation results
        enhanced_message = (
            f"{message}\n\n"
            f"[SYSTEM NOTE: The following subtasks were delegated to specialized agents:]\n\n"
            f"{delegation_summary}"
        )

        # Remove the original message we added earlier
        self.main_agent.conversation_history.pop()

        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] All delegated tasks complete, processing with main agent{Colors.ENDC}"
        )

        # Get main agent response with the enhanced message
        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Activated with delegation results{Colors.ENDC}"
        )
        response = self.main_agent.chat(enhanced_message, system_prompt, stream)
        print(f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Complete{Colors.ENDC}")

        return response

    def _handle_special_command(self, message: str) -> str:
        """Handle special orchestrator commands.

        Args:
            message: The command message

        Returns:
            Command response
        """
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Handling special command: {message}{Colors.ENDC}"
        )

        command_parts = message.lower().split()
        command = command_parts[0]

        if command == "/status":
            main_status = self.main_agent.get_status()
            active_agent_count = len(self.active_agents)

            return (
                f"Orchestrator Status:\n"
                f"- Main Agent Context: {main_status['estimated_tokens']:,} / {main_status['max_tokens']:,} tokens "
                f"({main_status['usage_percentage']:.1f}%)\n"
                f"- Message History: {main_status['messages']} messages ({main_status['exchanges']} exchanges)\n"
                f"- Active Transient Agents: {active_agent_count}/{self.max_agents}\n"
                f"- Recent Delegations: {len(self.transient_results)}\n\n"
                f"Available Commands:\n"
                f"- /status - Show this status\n"
                f"- /agents - List active transient agents\n"
                f"- /prune [n] - Keep only last n exchanges\n"
                f"- /clear - Clear entire conversation history"
            )

        elif command == "/agents":
            if not self.active_agents:
                return "No active transient agents."

            agent_info = []
            for task_id, agent in self.active_agents.items():
                agent_info.append(
                    f"- Agent {agent.agent_id}: {agent.task_description[:50]}... (Status: {agent.status})"
                )

            return "Active Transient Agents:\n" + "\n".join(agent_info)

        elif command == "/clear":
            print(
                f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Clearing conversation history{Colors.ENDC}"
            )
            cleared = self.main_agent.clear_history()
            self.transient_results = {}
            return f"Cleared {cleared} messages from conversation history and all transient agent results."

        elif command == "/prune":
            # Extract number if provided
            keep = 5  # Default
            if len(command_parts) > 1 and command_parts[1].isdigit():
                keep = int(command_parts[1])

            print(
                f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Pruning history to last {keep} exchanges{Colors.ENDC}"
            )
            pruned = self.main_agent.prune_history(keep)
            if pruned > 0:
                return f"Pruned {pruned} messages from history, keeping last {keep} exchanges."
            else:
                return f"No messages pruned. History already has {len(self.main_agent.conversation_history) // 2} exchanges."

        # Forward other commands to main agent
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Forwarding command to main agent{Colors.ENDC}"
        )
        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Activated for command handling{Colors.ENDC}"
        )
        response = self.main_agent.chat(message)
        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}[MAIN_AGENT] Command handling complete{Colors.ENDC}"
        )
        return response

    def _delegate_tasks(
        self, tasks: List[Dict[str, Any]], original_request: str
    ) -> List[Dict[str, Any]]:
        """Delegate tasks to transient agents.

        Args:
            tasks: List of tasks to delegate
            original_request: The original user request

        Returns:
            List of task results
        """
        results = []
        pending_tasks = []

        # Prepare context summary for delegation
        context_summary = self.context_manager.summarize_for_delegation(
            self.main_agent.conversation_history,
            "Process the following task based on this context summary",
            max_tokens=4000,
        )

        # Determine how many tasks to run concurrently
        concurrent_tasks = min(len(tasks), self.max_agents)

        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Delegating {len(tasks)} tasks "
            f"with {concurrent_tasks} concurrent agents{Colors.ENDC}"
        )

        # Set up the thread pool for running agents
        with ThreadPoolExecutor(max_workers=concurrent_tasks) as executor:
            # Submit all tasks to the executor
            for task in tasks:
                task_id = task["task_id"]

                # Log agent creation
                print(
                    f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Creating agent for task {task_id}{Colors.ENDC}"
                )
                print(
                    f"{Colors.BLUE}[ORCHESTRATOR] Task description: {task['description'][:100]}...{Colors.ENDC}"
                )

                # Create a transient agent for this task
                agent = TransientAgent(
                    task_id=task_id,
                    task_description=task["description"],
                    model=self.model,
                    api_base=self.api_base,
                    mcp_fs_url=self.mcp_fs_url,
                    system_prompt=self.transient_agent_prompt,
                )

                # Track the agent
                self.active_agents[task_id] = agent

                # Mark task as delegated
                task["delegated"] = True
                task["status"] = "in_progress"

                print(
                    f"{Colors.BLUE}[ORCHESTRATOR] Submitting task {task_id} to thread pool{Colors.ENDC}"
                )

                # Submit the task to the executor
                future = executor.submit(agent.execute, context_summary)
                pending_tasks.append((task_id, future))

            # Process results as they complete
            for task_id, future in pending_tasks:
                try:
                    # Wait for the task to complete
                    result = future.result()

                    # Update task status
                    for task in tasks:
                        if task["task_id"] == task_id:
                            task["status"] = "completed"
                            break

                    # Save the result
                    self.transient_results[task_id] = result
                    results.append(result)

                    print(
                        f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Task {task_id} completed successfully{Colors.ENDC}"
                    )
                    print(
                        f"{Colors.BLUE}[ORCHESTRATOR] Summary: {result['summary'][:100]}...{Colors.ENDC}"
                    )

                except Exception as e:
                    print(
                        f"{Colors.BG_RED}{Colors.BOLD}[ORCHESTRATOR] Task {task_id} failed: {str(e)}{Colors.ENDC}"
                    )

                    # Update task status
                    for task in tasks:
                        if task["task_id"] == task_id:
                            task["status"] = "failed"
                            break

                    # Add error result
                    error_result = {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "summary": f"Task failed: {str(e)}",
                    }
                    self.transient_results[task_id] = error_result
                    results.append(error_result)

                finally:
                    # Remove from active agents and log termination
                    if task_id in self.active_agents:
                        print(
                            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] Terminating agent for task {task_id}{Colors.ENDC}"
                        )
                        del self.active_agents[task_id]

        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}[ORCHESTRATOR] All {len(tasks)} tasks completed{Colors.ENDC}"
        )

        return results

    def _format_delegation_results(self, results: List[Dict[str, Any]]) -> str:
        """Format delegation results for the main agent.

        Args:
            results: List of task results

        Returns:
            Formatted results string
        """
        if not results:
            return "[No delegation results]"

        formatted_output = "## Delegation Results\n\n"

        for i, result in enumerate(results):
            task_id = result.get("task_id", f"unknown-{i}")
            status = result.get("status", "unknown")
            summary = result.get("summary", "No summary provided")

            formatted_output += f"### Task {i + 1}: {task_id}\n"
            formatted_output += f"**Status:** {status}\n\n"
            formatted_output += f"{summary}\n\n"

        return formatted_output
