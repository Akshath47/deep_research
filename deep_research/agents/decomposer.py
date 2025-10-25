"""
Decomposer Agent for Deep Research Multi-Agent System

This agent breaks down the clarified query into smaller, focused sub-queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepagents import create_deep_agent
from state import ResearchFlowState
from utils.prompts import DECOMPOSER_AGENT_PROMPT
from deep_research.config.models import get_model


def create_decomposer_agent():
    """
    Create the decomposer agent using the deepagents framework.
    
    The decomposer agent:
    - Reads: clarified_query.md
    - Writes: subqueries.json → structured list of sub-queries
    - Flow: Sequential (second step)
    """
    
    # No additional tools needed beyond the built-in file system tools
    tools = []
    
    # Create the agent with the decomposer prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=tools,
        instructions=DECOMPOSER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Only need the built-in file tools: write_file, read_file, ls, edit_file
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        model=get_model("decomposer")
    )
    
    return agent


# Create the agent instance
decomposer_agent = create_decomposer_agent()