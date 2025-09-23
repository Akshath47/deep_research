"""
Clarifier Agent for Deep Research Multi-Agent System

This agent asks clarifying questions and refines the original query into a crystal-clear research brief.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepagents import create_deep_agent, ToolInterruptConfig
from state import ResearchFlowState
from utils.prompts import CLARIFIER_AGENT_PROMPT
from tools.clarification import ask_clarifying_question, finalize_clarified_query


def create_clarifier_agent():
    """
    Create the clarifier agent using the deepagents framework.
    
    The clarifier agent:
    - Reads: User input
    - Writes: clarified_query.md → refined, unambiguous version of the query
    - Flow: Sequential (first step)
    - Uses human-in-the-loop for clarifying questions
    """
    
    # Custom tools for clarification workflow
    tools = [
        ask_clarifying_question,
        finalize_clarified_query
    ]
    
    # Configure interrupts for the clarifying question tool
    interrupt_config: ToolInterruptConfig = {
        "ask_clarifying_question": {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
            "allow_ignore": False,
        }
    }
    
    # Create the agent with the clarifier prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=tools,
        instructions=CLARIFIER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Include built-in file tools plus custom clarification tools
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        interrupt_config=interrupt_config
    )
    
    return agent


# Create the agent instance
clarifier_agent = create_clarifier_agent()