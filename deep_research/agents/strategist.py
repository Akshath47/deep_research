"""
Strategist Agent for Deep Research Multi-Agent System

This agent designs the research plan by expanding sub-queries into search strategies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepagents import create_deep_agent
from state import ResearchFlowState
from utils.prompts import STRATEGIST_AGENT_PROMPT
from deep_research.config.models import get_model


def create_strategist_agent():
    """
    Create the strategist agent using the deepagents framework.
    
    The strategist agent:
    - Reads: subqueries.json
    - Writes: research_plan.json → structured JSON plan with search strategies
    - Flow: Sequential (third step)
    
    The agent now outputs structured JSON instead of markdown for easier parsing
    by downstream components like the researcher agent.
    """
    
    # No additional tools needed beyond the built-in file system tools
    tools = []
    
    # Create the agent with the strategist prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=tools,
        instructions=STRATEGIST_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Only need the built-in file tools: write_file, read_file, ls, edit_file
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        model=get_model("strategist")
    )
    
    return agent


# Create the agent instance
strategist_agent = create_strategist_agent()