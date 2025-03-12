# Hierarchical Agent Architecture

This document explains the hierarchical agent architecture implemented to handle complex tasks while efficiently managing context size.

## Overview

The hierarchical agent system uses a main "orchestrator" agent that coordinates with temporary "transient" agents to handle complex tasks. When a user request requires multiple operations that would fill up the context window, the system delegates specific subtasks to transient agents that execute independently and return summarized results.

## Key Components

### Agent Orchestrator

The central coordinator that:
- Analyzes user requests to determine complexity
- Creates task plans for complex requests
- Delegates subtasks to transient agents
- Integrates results into coherent responses
- Manages context size and history

### Transient Agents

Specialized temporary agents that:
- Focus on singular, well-defined tasks
- Execute with clean context windows
- Process file operations and MCP commands
- Summarize results concisely for the main agent
- Are destroyed after task completion

### Context Manager

Utility that handles:
- Token usage estimation
- Context pruning strategies
- Summarization for delegation
- Warning about context limitations

### Task Planner

Component responsible for:
- Analyzing request complexity
- Breaking down requests into discrete tasks
- Determining which tasks to delegate
- Creating structured task plans

## Workflow

1. User sends a request to the system
2. Orchestrator analyzes request complexity
3. For simple requests, main agent handles directly
4. For complex requests:
   - Task planner creates subtasks
   - Orchestrator delegates appropriate subtasks to transient agents
   - Transient agents execute their tasks independently
   - Results are summarized and returned to orchestrator
   - Main agent processes all results into a coherent response
5. Final response is presented to the user

## Context Management

The system employs several strategies to manage context size:
- Selective delegation of high-context operations
- Smart pruning of conversation history
- Removing file operation details from history
- Summarization of older exchanges
- Context usage monitoring and warnings

## Special Commands

The architecture supports several special commands:
- `/status` - Display context usage and agent status
- `/agents` - List active transient agents
- `/prune [n]` - Keep only last n conversation exchanges
- `/clear` - Reset conversation history

## Visual Indicators

Terminal output includes color-coded indicators:
- Blue for orchestrator operations
- Green for transient agent activities  
- Yellow for context warnings
- Red for critical errors and context alerts
- Magenta for task planning operations

## Advantages

- Maintains coherent conversation with users while handling complex tasks
- Prevents context overflow during multi-step operations
- Enables parallel processing of subtasks
- Provides more efficient use of token capacity
- Improves response times for complex operations