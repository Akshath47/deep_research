"""
Synthesizer Agent for Deep Research Multi-Agent System

This agent synthesizes research findings into a comprehensive report following
a sequential workflow with mandatory inline citations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from deepagents import create_deep_agent
from state import ResearchFlowState
from utils.prompts import SYNTHESIZER_AGENT_PROMPT
from deep_research.config.models import get_model


def create_synthesizer_agent():
    """
    Create the synthesizer agent using the deepagents framework.
    
    The synthesizer agent:
    - Reads: clarified_query.md, /summaries/*, factcheck_notes.md, /raw_data/* (fallback)
    - Writes: draft_report.md → structured paper with inline citations [1], [2], ...
    - Flow: Sequential (runs after fact-checker)
    - Implements mandatory inline citation system with numerical format
    - Generates complete citations index organized by URL
    """
    
    # Create the agent with the synthesizer prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=[],  # No custom tools needed, just built-in file operations
        instructions=SYNTHESIZER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Include built-in file tools for reading inputs and writing report
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        model=get_model("synthesizer")
    )
    
    return agent


# Create the agent instance
synthesizer_agent = create_synthesizer_agent()