"""Task planning and decomposition for hierarchical agents."""

from typing import Dict, List, Any, Tuple, Optional
import re
import uuid

from terminal_utils import Colors


# TODO: This class is a mess. Hardcoded rules that aren't useful.
# Summarising the wikipedia page of a book would be considered a complex task
# Writing an advanced GPU algorithm would be considered trivial w/ no required planning
# This needs to be replaced with a lightweight model that decomposes tasks
# PRIORITY: HIGH
class TaskPlanner:
    """Plans and decomposes complex user requests into discrete tasks."""

    def __init__(self):
        """Initialize the TaskPlanner."""
        pass

    def analyze_request(self, user_message: str) -> Dict[str, Any]:
        """Analyze a user request to determine if it should be decomposed.

        Args:
            user_message: The user's request message

        Returns:
            Dictionary with analysis results:
            {
                "requires_planning": bool,
                "complexity": "simple"|"medium"|"complex",
                "potential_subtasks": List[str],
                "estimated_resource_usage": "low"|"medium"|"high"
            }
        """
        result = {
            "requires_planning": False,
            "complexity": "simple",
            "potential_subtasks": [],
            "estimated_resource_usage": "low",
        }

        # Check message length as initial complexity indicator
        if len(user_message) > 1000:
            result["complexity"] = "complex"
            result["estimated_resource_usage"] = "high"
            result["requires_planning"] = True
        elif len(user_message) > 500:
            result["complexity"] = "medium"
            result["estimated_resource_usage"] = "medium"

        # Look for indicators of file operations
        file_operations = 0
        file_operations += len(
            re.findall(
                r"(?:read|write|check|view|open|update).*file",
                user_message,
                re.IGNORECASE,
            )
        )
        file_operations += len(
            re.findall(r"content(?:s)? of.*\.[a-z]+", user_message, re.IGNORECASE)
        )

        # Look for search operations
        search_operations = 0
        search_operations += len(
            re.findall(
                r"(?:search|find|look for|locate|grep)", user_message, re.IGNORECASE
            )
        )

        # Increment required planning based on operation counts
        if file_operations > 3 or search_operations > 2:
            result["complexity"] = "complex"
            result["estimated_resource_usage"] = "high"
            result["requires_planning"] = True
        elif file_operations > 1 or search_operations > 0:
            result["complexity"] = "medium"
            result["estimated_resource_usage"] = "medium"

            # Only require planning for medium complexity if there are multiple operations
            if file_operations + search_operations > 2:
                result["requires_planning"] = True

        # Check for phrases suggesting complex operations
        complex_indicators = [
            "refactor",
            "restructure",
            "implement",
            "create a new",
            "analyze",
            "compare",
            "optimize",
            "fix",
            "debug",
            "add feature",
            "multiple files",
        ]

        for indicator in complex_indicators:
            if re.search(
                r"\b" + re.escape(indicator) + r"\b", user_message, re.IGNORECASE
            ):
                result["complexity"] = "complex"
                result["estimated_resource_usage"] = "high"
                result["requires_planning"] = True
                break

        # Generate potential subtasks based on identified operations
        if result["requires_planning"]:
            result["potential_subtasks"] = self._generate_potential_subtasks(
                user_message, file_operations, search_operations
            )

        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}TASK ANALYSIS: {result['complexity']} complexity, "
            f"{'requires' if result['requires_planning'] else 'does not require'} planning, "
            f"{len(result['potential_subtasks'])} potential subtasks{Colors.ENDC}"
        )

        return result

    def _generate_potential_subtasks(
        self, user_message: str, file_operations: int, search_operations: int
    ) -> List[str]:
        """Generate potential subtasks based on user message and operation counts.

        Args:
            user_message: The user message to analyze
            file_operations: Count of detected file operations
            search_operations: Count of detected search operations

        Returns:
            List of potential subtask descriptions
        """
        subtasks = []

        # Add information gathering subtasks if search operations
        if search_operations > 0:
            subtasks.append(
                "Information gathering: Search for relevant files and code sections"
            )

        # Add code reading subtasks if file operations
        if file_operations > 0:
            subtasks.append("Code analysis: Read and understand relevant files")

        # Look for specific file extensions mentioned
        file_extensions = re.findall(
            r"\b\w+\.(py|js|java|cpp|h|json|yaml|yml|md|txt)\b", user_message
        )
        if file_extensions:
            unique_extensions = set(file_extensions)
            file_types = ", ".join(unique_extensions)
            subtasks.append(
                f"File processing: Handle {file_types} files mentioned in request"
            )

        # Look for potential implementation tasks
        if re.search(
            r"\b(implement|create|add|develop)\b", user_message, re.IGNORECASE
        ):
            subtasks.append(
                "Code implementation: Write or modify code based on requirements"
            )

        # Look for potential testing tasks
        if re.search(r"\b(test|verify|validate|check)\b", user_message, re.IGNORECASE):
            subtasks.append("Testing: Verify changes work as expected")

        # If we couldn't identify specific subtasks, add generic ones
        if not subtasks:
            subtasks = [
                "Analyze user request and determine approach",
                "Gather necessary information",
                "Execute required actions",
                "Verify results and prepare response",
            ]

        return subtasks

    def create_task_plan(
        self, user_message: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a concrete task plan based on user message and analysis.

        Args:
            user_message: The original user message
            analysis: The result from analyze_request()

        Returns:
            Task plan dictionary with:
            {
                "plan_id": str,
                "original_request": str,
                "requires_delegation": bool,
                "tasks": [
                    {
                        "task_id": str,
                        "description": str,
                        "delegated": bool,
                        "status": "pending"|"in_progress"|"completed"|"failed",
                        "delegate_to_transient": bool
                    },
                    ...
                ]
            }
        """
        plan_id = str(uuid.uuid4())[:8]  # Generate a short unique ID

        plan = {
            "plan_id": plan_id,
            "original_request": user_message,
            "requires_delegation": analysis["requires_planning"],
            "tasks": [],
        }

        # If planning not required, create a single task for the main agent
        if not analysis["requires_planning"]:
            plan["tasks"].append(
                {
                    "task_id": f"{plan_id}-1",
                    "description": "Process user request directly",
                    "delegated": False,
                    "status": "pending",
                    "delegate_to_transient": False,
                }
            )
            return plan

        # For more complex requests, build a task list based on the analysis
        task_count = 0

        for subtask in analysis["potential_subtasks"]:
            task_count += 1
            task_id = f"{plan_id}-{task_count}"

            # Determine if this subtask should be delegated
            delegate = False

            # Information gathering and search tasks are good candidates for delegation
            if "search" in subtask.lower() or "gather" in subtask.lower():
                delegate = True

            # Reading multiple files is also good for delegation
            if "read" in subtask.lower() and "multiple" in subtask.lower():
                delegate = True

            # Add the task to our plan
            plan["tasks"].append(
                {
                    "task_id": task_id,
                    "description": subtask,
                    "delegated": False,  # Will be set to True when actually delegated
                    "status": "pending",
                    "delegate_to_transient": delegate,
                }
            )

        print(
            f"{Colors.BG_MAGENTA}{Colors.BOLD}TASK PLAN CREATED: Plan #{plan_id} with "
            f"{len(plan['tasks'])} tasks, {sum(1 for t in plan['tasks'] if t['delegate_to_transient'])} "
            f"marked for delegation{Colors.ENDC}"
        )

        return plan
