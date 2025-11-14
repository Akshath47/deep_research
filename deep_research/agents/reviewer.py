"""
Reviewer Agent for Deep Research Multi-Agent System

This agent performs final quality assurance, completeness checking, clarity review,
and gap detection. It produces a polished final report and a structured gap list
for future research iterations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from deepagents import create_deep_agent
from state import ResearchFlowState
from utils.prompts import REVIEWER_AGENT_PROMPT
from config.models import get_model


def create_reviewer_agent():
    """
    Create the reviewer agent using the deepagents framework.
    
    The reviewer agent:
    - Reads: draft_report.md, subqueries.json, /summaries/* (optional), factcheck_notes.md (optional)
    - Writes: final_paper.md (polished report), gap_list.json (structured gap analysis)
    - Flow: Sequential (runs after synthesizer, final stage)
    - Performs: Completeness check, clarity review, conservative gap filling, gap detection
    
    Key responsibilities:
    1. Verify every sub-query from the research plan has been addressed
    2. Evaluate clarity and logical structure of the report
    3. Fill minor gaps when information can be inferred from existing sources
    4. Document moderate and major gaps in structured JSON format
    5. Generate polished final report maintaining academic standards
    6. Create actionable gap list for future research iterations
    
    Conservative gap filling principles:
    - Only fill gaps when information is explicitly stated in summaries
    - No speculation or assumptions beyond source material
    - Maintain source fidelity and citation accuracy
    - Refrain from introducing knowledge not grounded in research
    """
    
    # Create the agent with the reviewer prompt and ResearchFlowState
    agent = create_deep_agent(
        tools=[],  # No custom tools needed, just built-in file operations
        instructions=REVIEWER_AGENT_PROMPT,
        state_schema=ResearchFlowState,
        # Include built-in file tools for reading inputs and writing outputs
        builtin_tools=["write_file", "read_file", "ls", "edit_file"],
        model=get_model("reviewer")
    )
    
    return agent


# Create the agent instance
reviewer_agent = create_reviewer_agent()