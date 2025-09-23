"""
Custom tools for the clarifier agent to enable human-in-the-loop interactions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import List, Annotated
from langgraph.prebuilt import InjectedState
from state import ResearchFlowState


@tool
def ask_clarifying_question(
    questions: List[str],
    state: Annotated[ResearchFlowState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Ask clarifying questions to the user and wait for their response.
    
    Args:
        questions: List of clarifying questions to ask the user (max 3 questions)
    
    Returns:
        Command that will trigger human interrupt for questions
    """
    if len(questions) > 3:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        "Error: Maximum 3 clarifying questions allowed per interaction",
                        tool_call_id=tool_call_id
                    )
                ]
            }
        )
    
    # Format the questions nicely
    question_text = "I need some clarification to better understand your research needs:\n\n"
    for i, question in enumerate(questions, 1):
        question_text += f"{i}. {question}\n"
    
    question_text += "\nPlease provide your answers to help me refine your research query."
    
    # Return the formatted questions - the interrupt will be handled by the agent's interrupt config
    return Command(
        update={
            "messages": [
                ToolMessage(question_text, tool_call_id=tool_call_id)
            ]
        }
    )


@tool
def finalize_clarified_query(
    original_query: str,
    clarifications: str,
    refined_query: str,
    scope: str,
    key_questions: List[str],
    state: Annotated[ResearchFlowState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    constraints: str = "",
    deliverable_format: str = "comprehensive research report"
) -> Command:
    """
    Finalize the clarified research query and save it to clarified_query.md.
    
    Args:
        original_query: The user's original research question
        clarifications: Summary of clarifications received from the user
        refined_query: The refined, unambiguous research objective
        scope: Specific scope and boundaries of the research
        key_questions: List of key questions to be answered
        constraints: Any constraints or requirements
        deliverable_format: Expected format of the final deliverable
    
    Returns:
        Command that updates the state with the clarified query
    """
    
    # Create the clarified query document
    clarified_content = f"""# Clarified Research Query

## Original Query
{original_query}

## Clarifications Received
{clarifications}

## Refined Research Objective
{refined_query}

## Research Scope and Boundaries
{scope}

## Key Questions to Answer
"""
    
    for i, question in enumerate(key_questions, 1):
        clarified_content += f"{i}. {question}\n"
    
    if constraints:
        clarified_content += f"""
## Constraints and Requirements
{constraints}
"""
    
    clarified_content += f"""
## Expected Deliverable Format
{deliverable_format}

## Research Brief Summary
This research will focus on: {refined_query}

The research scope includes: {scope}

The final deliverable will be: {deliverable_format}
"""
    
    # Update the files in state
    files = dict(state.get("files", {}))
    files["clarified_query.md"] = clarified_content
    
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(
                    f"Successfully created clarified research query and saved to 'clarified_query.md'",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )