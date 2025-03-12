"""Context management utilities for testing."""

from typing import Dict, List, Any, Tuple
import re

from tests.mocks.terminal_utils_context import Colors


class ContextManager:
    """Manages LLM context size and intelligent pruning of conversation history."""

    def __init__(self, max_context_tokens: int = 32000, token_ratio: int = 4):
        """Initialize a ContextManager instance.
        
        Args:
            max_context_tokens: Maximum token capacity for the model
            token_ratio: Approximation ratio for token estimation (chars/token)
        """
        self.max_context_tokens = max_context_tokens
        self.token_ratio = token_ratio
        self.warning_threshold = 0.7  # Warn at 70% context usage
        self.critical_threshold = 0.9  # Critical warning at 90% context usage
        
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        This is a simple approximation - more accurate token counting
        would require a tokenizer specific to the model being used.
        
        Args:
            text: The text to estimate token count for
            
        Returns:
            Estimated token count
        """
        return len(text) // self.token_ratio
    
    def check_context_size(self, 
                           history: List[Dict[str, str]], 
                           system_prompt: str = None) -> Tuple[str, int, float]:
        """Check if the current context size is approaching token limits.
        
        Args:
            history: Conversation history to check
            system_prompt: Optional system prompt to include in calculation
            
        Returns:
            Tuple of (status, estimated_tokens, usage_percentage)
            where status is one of "ok", "warning", "critical"
        """
        # Estimate token count for the entire history
        total_chars = sum(len(msg["content"]) for msg in history)
        estimated_tokens = total_chars // self.token_ratio
        
        # Account for system prompt if present
        if system_prompt:
            system_tokens = len(system_prompt) // self.token_ratio
            estimated_tokens += system_tokens
        
        # Calculate percentage of max context used
        usage_percentage = estimated_tokens / self.max_context_tokens
        
        # Determine status based on thresholds
        if usage_percentage >= self.critical_threshold:
            status = "critical"
            print(
                f"{Colors.BG_RED}{Colors.BOLD}CRITICAL: Context size at {usage_percentage:.1%} "
                f"({estimated_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
            )
        elif usage_percentage >= self.warning_threshold:
            status = "warning"
            print(
                f"{Colors.BG_YELLOW}{Colors.BOLD}WARNING: Context size at {usage_percentage:.1%} "
                f"({estimated_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
            )
        else:
            status = "ok"
            print(
                f"{Colors.CYAN}Context size: {usage_percentage:.1%} "
                f"({estimated_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
            )
        
        return status, estimated_tokens, usage_percentage
    
    def smart_prune_history(self, 
                           history: List[Dict[str, str]], 
                           target_percentage: float = 0.6) -> List[Dict[str, str]]:
        """Intelligently prune history to target percentage of max context.
        
        This method performs selective pruning, focusing on:
        1. Removing detailed results from previous commands
        2. Summarizing long user inputs
        3. Maintaining the most recent exchanges intact
        
        Args:
            history: Conversation history to prune
            target_percentage: Target percentage of max context to keep
            
        Returns:
            Pruned conversation history
        """
        if not history:
            return []
        
        # Check current size
        _, current_tokens, current_percentage = self.check_context_size(history)
        
        # If already below target, no pruning needed
        if current_percentage <= target_percentage:
            return history
        
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}SMART PRUNING: Reducing context from {current_percentage:.1%} to target {target_percentage:.1%}{Colors.ENDC}"
        )
        
        # Make a copy of history to avoid modifying the original
        working_history = history.copy()
        
        # Calculate target token count
        target_tokens = int(self.max_context_tokens * target_percentage)
        
        # STEP 1: Remove file operation results from assistant responses
        for i, msg in enumerate(working_history):
            if msg["role"] == "assistant" and i < len(working_history) - 2:  # Preserve most recent response
                # Remove file content blocks
                content = msg["content"]
                
                # Look for patterns like "--- Content of file.txt ---" with content until "---"
                content = re.sub(
                    r"---\s+Content of[^-]+---\s+.*?---",
                    "[File content removed during context pruning]",
                    content,
                    flags=re.DOTALL
                )
                
                # Look for patterns like "--- Contents of directory /path ---" with content until "---"
                content = re.sub(
                    r"---\s+Contents of directory[^-]+---\s+.*?---",
                    "[Directory listing removed during context pruning]",
                    content,
                    flags=re.DOTALL
                )
                
                # Look for patterns like "--- Search results for 'pattern' ---" with content until "---"
                content = re.sub(
                    r"---\s+(?:Search|Grep) results for[^-]+---\s+.*?---",
                    "[Search results removed during context pruning]",
                    content,
                    flags=re.DOTALL
                )
                
                # Update the message content
                working_history[i]["content"] = content
        
        # Check if we've reached target
        _, current_tokens, current_percentage = self.check_context_size(working_history)
        if current_percentage <= target_percentage:
            print(
                f"{Colors.GREEN}Successfully pruned context to {current_percentage:.1%} "
                f"({current_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
            )
            return working_history
            
        # STEP 2: Summarize older user messages (except the most recent 2 exchanges)
        for i, msg in enumerate(working_history):
            # Preserve the most recent 2 exchanges (4 messages: 2 user, 2 assistant)
            if i < len(working_history) - 4 and msg["role"] == "user":
                content = msg["content"]
                
                # If the message is long, summarize it
                if len(content) > 500:
                    # Keep the first 200 chars as context
                    summary = content[:200]
                    # Add a note that content was truncated
                    summary += f"... [User message truncated from {len(content)} characters during context pruning]"
                    working_history[i]["content"] = summary
        
        # Check if we've reached target
        _, current_tokens, current_percentage = self.check_context_size(working_history)
        if current_percentage <= target_percentage:
            print(
                f"{Colors.GREEN}Successfully pruned context to {current_percentage:.1%} "
                f"({current_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
            )
            return working_history
            
        # STEP 3: If still above target, remove oldest exchanges (preserving most recent 2)
        keep_count = 4  # Start by keeping just the most recent 2 exchanges
        while keep_count < len(working_history) and current_percentage > target_percentage:
            # Remove the oldest exchange
            working_history = working_history[2:]  # Remove oldest user + assistant pair
            
            # Check if we've reached target
            _, current_tokens, current_percentage = self.check_context_size(working_history)
            if current_percentage <= target_percentage:
                break
            
        print(
            f"{Colors.GREEN}Pruned history to {len(working_history)} messages, "
            f"context size now {current_percentage:.1%} "
            f"({current_tokens:,}/{self.max_context_tokens:,} tokens){Colors.ENDC}"
        )
        
        return working_history
    
    def summarize_for_delegation(self, 
                               history: List[Dict[str, str]], 
                               task_description: str,
                               max_tokens: int = 2000) -> str:
        """Summarize conversation history for delegating to a transient agent.
        
        Creates a compact summary of relevant history to pass to a transient agent,
        focused on the current task while staying under token limits.
        
        Args:
            history: Conversation history to summarize
            task_description: Description of the task being delegated
            max_tokens: Maximum tokens to use for the summary
            
        Returns:
            A summarized context string for the transient agent
        """
        # Determine the estimated token budget
        max_chars = max_tokens * self.token_ratio
        
        # Start with a task description
        summary = f"# DELEGATED TASK\n{task_description}\n\n"
        
        # Add the most recent user message first (most relevant)
        if history and history[-1]["role"] == "user":
            summary += f"# CURRENT USER REQUEST\n{history[-1]['content']}\n\n"
        
        # Add system prompt if available in history (assuming first message is system)
        if history and len(history) > 0:
            first_msg = history[0]
            if first_msg.get("role") == "system":
                summary += f"# SYSTEM PROMPT\n{first_msg['content']}\n\n"
        
        # Add previous exchanges that might be relevant
        # Start with the most recent and work backwards
        summary += "# RELEVANT HISTORY\n"
        
        # Track how much space we've used
        current_chars = len(summary)
        
        # Iterate from most recent to oldest, excluding the current user message
        for i in range(len(history) - 2, -1, -1):
            msg = history[i]
            
            # Skip system prompt as we've already added it
            if msg.get("role") == "system":
                continue
                
            # Format the message
            msg_text = f"{msg['role'].upper()}: {msg['content']}\n\n"
            
            # Check if adding this message would exceed our limit
            if current_chars + len(msg_text) > max_chars:
                # If we're about to exceed, add a note and stop
                summary += "\n[Earlier history omitted to stay within context limits]"
                break
                
            # Add this message to our summary
            summary += msg_text
            current_chars += len(msg_text)
        
        # Calculate token estimate for the summary
        estimated_tokens = self.estimate_tokens(summary)
        print(
            f"{Colors.BG_BLUE}{Colors.BOLD}CONTEXT SUMMARY: {estimated_tokens:,} tokens "
            f"({len(summary):,} chars) prepared for delegation{Colors.ENDC}"
        )
        
        return summary