"""Context summarization module for managing large conversation histories.

This module provides functionality to compress conversation history when it exceeds
the model's context window, using a smaller but more efficient model to summarize
conversation threads while preserving critical information.
"""

import requests
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from terminal_utils import Colors


class ContextSummarizer:
    """Summarizes conversation history to fit within context limits."""

    def __init__(
        self,
        model="gemma3:12b",
        api_base="http://localhost:11434",
        max_context_tokens=32000,
        token_estimate_ratio=4,
    ):
        """Initialize the context summarizer.
        
        Args:
            model: Ollama model to use for summarization
            api_base: URL for the Ollama API
            max_context_tokens: Maximum context window for the summarization model
            token_estimate_ratio: Approximate characters per token ratio
        """
        self.model = model
        self.api_base = api_base
        self.max_context_tokens = max_context_tokens
        self.token_estimate_ratio = token_estimate_ratio
        
        # Load system prompt for summarization
        self.system_prompt = self._get_summarization_prompt()
        
        print(f"{Colors.BG_GREEN}{Colors.BOLD}[SUMMARIZER] Initialized with model {model}{Colors.ENDC}")
    
    def _get_summarization_prompt(self) -> str:
        """Get the system prompt for the summarization model."""
        return """You are a Context Summarizer, specializing in compressing conversation history while preserving critical information.

Your task is to analyze the given conversation history and produce a condensed summary that:
1. Preserves all MCP command results and important file content
2. Maintains the key points and decisions from the conversation
3. Removes redundant information and pleasantries
4. Structures information in a way that the main agent can easily understand
5. Keeps important code snippets and technical details intact

FORMAT YOUR RESPONSE AS FOLLOWS:
- Start with "## Conversation Summary"
- Include section "### System Context" for key system information
- Include section "### Command Results" for all MCP command outputs
- Include section "### Key Decisions" for important decisions or conclusions
- End with a very brief "### Next Steps" suggesting what should be addressed next

EXTREMELY IMPORTANT: 
- NEVER remove MCP command results
- When a file is viewed, ALWAYS keep the file content
- NEVER remove code blocks or technical details
- Preserve the context related to the current programming task
- Make sure your summary is comprehensive enough that the conversation can continue naturally
"""
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string.
        
        Args:
            text: Text to estimate token count for
            
        Returns:
            Estimated token count
        """
        return len(text) // self.token_estimate_ratio
    
    def _extract_mcp_results(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract MCP command results from conversation history.
        
        This function identifies and extracts all command results to ensure
        they're preserved in the summarized context.
        
        Args:
            history: Conversation history
            
        Returns:
            List of extracted command result blocks
        """
        command_results = []
        
        for msg in history:
            content = msg.get("content", "")
            
            # Look for command result patterns
            result_blocks = re.findall(
                r"---\s+(Content of|Contents of directory|Search results for|Grep results for)[\s\S]+?---",
                content,
                re.DOTALL
            )
            
            for block in result_blocks:
                command_results.append(block)
        
        return command_results
    
    def _extract_code_blocks(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract code blocks from conversation history.
        
        Args:
            history: Conversation history
            
        Returns:
            List of extracted code blocks
        """
        code_blocks = []
        
        for msg in history:
            content = msg.get("content", "")
            
            # Extract code blocks (```...```)
            blocks = re.findall(r"```[\s\S]+?```", content, re.DOTALL)
            
            for block in blocks:
                code_blocks.append(block)
        
        return code_blocks
    
    def summarize_history(
        self, history: List[Dict[str, str]], preserve_recent: int = 2
    ) -> Tuple[List[Dict[str, str]], bool]:
        """Summarize conversation history to fit within context limits.
        
        Args:
            history: Conversation history to summarize
            preserve_recent: Number of most recent exchanges to preserve untouched
            
        Returns:
            Tuple of (summarized history, success flag)
        """
        print(f"{Colors.BG_GREEN}{Colors.BOLD}[SUMMARIZER] Beginning context summarization{Colors.ENDC}")
        
        # Keep the most recent exchanges intact (each exchange is user + assistant)
        preserved_msgs = min(preserve_recent * 2, len(history))
        history_to_summarize = history[:-preserved_msgs] if preserved_msgs > 0 else history.copy()
        recent_history = history[-preserved_msgs:] if preserved_msgs > 0 else []
        
        # If nothing to summarize, return original history
        if not history_to_summarize:
            print(f"{Colors.GREEN}[SUMMARIZER] No history to summarize{Colors.ENDC}")
            return history, True
        
        # Extract command results and code blocks to ensure preservation
        command_results = self._extract_mcp_results(history_to_summarize)
        code_blocks = self._extract_code_blocks(history_to_summarize)
        
        # Format history for summarization
        formatted_history = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content']}" for msg in history_to_summarize
        ])
        
        # Create the summarization prompt
        prompt = (
            f"Below is a conversation history that needs to be summarized while preserving key information:\n\n"
            f"{formatted_history}\n\n"
            f"IMPORTANT NOTES FOR SUMMARIZATION:\n"
            f"1. There are {len(command_results)} command result blocks that must be preserved\n"
            f"2. There are {len(code_blocks)} code blocks that should be preserved\n"
            f"3. Focus on key technical details and decisions\n"
            f"4. The summary will replace all previous conversation except the {preserve_recent} most recent exchanges\n"
            f"Please provide a comprehensive summary following the format in your instructions."
        )
        
        # Call the summarization model
        print(f"{Colors.GREEN}[SUMMARIZER] Calling {self.model} for summarization{Colors.ENDC}")
        print(f"{Colors.GREEN}[SUMMARIZER] Original history length: {len(formatted_history)} chars{Colors.ENDC}")
        
        try:
            # Make request to Ollama API
            endpoint = f"{self.api_base}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": self.system_prompt,
                "stream": False
            }
            
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            
            summary = result.get("response", "")
            print(f"{Colors.GREEN}[SUMMARIZER] Received summary of {len(summary)} chars{Colors.ENDC}")
            
            # Create a new history with the summary as the first message
            summarized_history = [
                {"role": "system", "content": f"CONTEXT SUMMARY: {summary}"}
            ]
            
            # Add back recent messages that were preserved
            summarized_history.extend(recent_history)
            
            print(f"{Colors.BG_GREEN}{Colors.BOLD}[SUMMARIZER] Successfully summarized context. "
                  f"Reduced from {len(history)} to {len(summarized_history)} messages{Colors.ENDC}")
            
            return summarized_history, True
            
        except Exception as e:
            print(f"{Colors.BG_RED}{Colors.BOLD}[SUMMARIZER] Error during summarization: {str(e)}{Colors.ENDC}")
            # Return original history on error
            return history, False

def apply_context_summarization(
    history: List[Dict[str, str]], 
    current_model_limit: int,
    token_estimate_ratio: int = 4,
    preserve_recent: int = 2,
    system_prompt: Optional[str] = None,
    summarizer: Optional[ContextSummarizer] = None
) -> Tuple[List[Dict[str, str]], bool, bool]:
    """Apply context summarization if needed based on token limits.
    
    Args:
        history: Conversation history
        current_model_limit: Token limit of the main model
        token_estimate_ratio: Approximate characters per token ratio
        preserve_recent: Number of most recent exchanges to preserve
        system_prompt: System prompt that will be added (for size calculation)
        summarizer: Optional existing summarizer object
        
    Returns:
        Tuple of (updated history, needs_summary, was_summarized)
    """
    # Calculate total tokens
    total_chars = sum(len(msg.get("content", "")) for msg in history)
    system_chars = len(system_prompt) if system_prompt else 0
    estimated_tokens = (total_chars + system_chars) // token_estimate_ratio
    
    # Check if summarization is needed (if we're over 90% capacity)
    needs_summary = estimated_tokens > (current_model_limit * 0.9)
    
    if not needs_summary:
        return history, False, False
    
    print(f"{Colors.BG_YELLOW}{Colors.BOLD}Context size ({estimated_tokens} tokens) exceeds model limit "
          f"({current_model_limit} tokens). Applying summarization...{Colors.ENDC}")
    
    # Create or use existing summarizer
    if summarizer is None:
        summarizer = ContextSummarizer()
    
    # Summarize history
    new_history, success = summarizer.summarize_history(history, preserve_recent)
    
    return new_history, needs_summary, success