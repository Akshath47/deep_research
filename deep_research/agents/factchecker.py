"""
Fact-Checker Agent for Deep Research Multi-Agent System

This agent cross-checks facts, detects contradictions, and filters out unreliable claims.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from deepagents import create_deep_agent
from state import ResearchFlowState
from utils.prompts import FACTCHECKER_AGENT_PROMPT
from config.models import get_model


def create_factchecker_agent():
    """
    Create the fact-checker agent using the deepagents framework.
    
    The fact-checker agent:
    - Reads: /summaries/* and /raw_data/* files
    - Writes: factcheck_notes.md → list of verified claims, contradictions, flagged weak sources
    - Flow: Sequential (runs after Researcher outputs are gathered)
    - Does NOT modify any existing summaries or raw data
    """
    
    # Create the agent with the fact-checker prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=[],  # No custom tools needed, just built-in file operations
        instructions=FACTCHECKER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Include built-in file tools for reading summaries/raw data and writing fact-check report
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        model=get_model("factchecker")
    )
    
    return agent


# Create the agent instance
factchecker_agent = create_factchecker_agent()