"""
Clarifier Agent for Deep Research Multi-Agent System

This agent asks clarifying questions and refines the original query into a crystal-clear research brief.
"""

from deepagents import create_deep_agent
from deep_research.state import ResearchFlowState
from deep_research.utils.prompts import CLARIFIER_AGENT_PROMPT


def create_clarifier_agent():
    """
    Create the clarifier agent using the deepagents framework.
    
    The clarifier agent:
    - Reads: User input
    - Writes: clarified_query.md → refined, unambiguous version of the query
    - Flow: Sequential (first step)
    """
    
    # No additional tools needed beyond the built-in file system tools
    tools = []
    
    # Create the agent with the clarifier prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=tools,
        instructions=CLARIFIER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Only need the built-in file tools: write_file, read_file, ls, edit_file
        builtin_tools=["write_file", "read_file", "ls", "edit_file"]
    )
    
    return agent


# Create the agent instance
clarifier_agent = create_clarifier_agent()