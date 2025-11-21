"""
Enhanced workflow with metadata emission for frontend tracking.

This version adds custom metadata events to support real-time UI updates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copy import deepcopy
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from state import ResearchFlowState
from deepagents.state import file_reducer

# Import all agent instances
from agents.clarifier import clarifier_agent
from agents.decomposer import decomposer_agent
from agents.strategist import strategist_agent
from agents.researcher import researcher_agent
from agents.factchecker import factchecker_agent
from agents.synthesizer import synthesizer_agent
from agents.reviewer import reviewer_agent
from graphs.researcher_hub import researcher_hub_graph


# Agent metadata for frontend
AGENT_METADATA = {
    "clarifier": {
        "display_name": "Clarifier",
        "description": "Analyzing query for ambiguities",
        "status_message": "Analyzing query...",
        "icon": "search"
    },
    "decomposer": {
        "display_name": "Decomposer",
        "description": "Breaking down into sub-questions",
        "status_message": "Decomposing query...",
        "icon": "split"
    },
    "strategist": {
        "display_name": "Strategist",
        "description": "Planning research strategy",
        "status_message": "Planning strategy...",
        "icon": "target"
    },
    "researcher_hub": {
        "display_name": "Researcher Hub",
        "description": "Conducting parallel research",
        "status_message": "Researching in parallel...",
        "icon": "users"
    },
    "fact_checker": {
        "display_name": "Fact Checker",
        "description": "Verifying facts and contradictions",
        "status_message": "Checking facts...",
        "icon": "check-circle"
    },
    "synthesizer": {
        "display_name": "Synthesizer",
        "description": "Synthesizing comprehensive report",
        "status_message": "Synthesizing report...",
        "icon": "file-text"
    },
    "reviewer": {
        "display_name": "Reviewer",
        "description": "Final quality checks",
        "status_message": "Reviewing results...",
        "icon": "eye"
    }
}


def run_agent_with_metadata(agent, state: ResearchFlowState, agent_name: str):
    """
    Run agent and add metadata for frontend tracking.
    """
    metadata = AGENT_METADATA.get(agent_name, {})

    # Add metadata to state for streaming
    state_with_metadata = {**state, "__metadata__": {
        "agent": agent_name,
        "display_name": metadata.get("display_name", agent_name),
        "status": "running",
        "message": metadata.get("status_message", f"Running {agent_name}")
    }}

    # Run the agent
    result = agent.invoke(state)

    # Merge files
    merged_files = {**state.get("files", {}), **result.get("files", {})}

    # Add completion metadata
    return {
        "files": merged_files,
        "__metadata__": {
            "agent": agent_name,
            "status": "completed"
        }
    }


# Individual agent runners with metadata
def run_clarifier(state: ResearchFlowState):
    return run_agent_with_metadata(clarifier_agent, state, "clarifier")

def run_decomposer(state: ResearchFlowState):
    return run_agent_with_metadata(decomposer_agent, state, "decomposer")

def run_strategist(state: ResearchFlowState):
    return run_agent_with_metadata(strategist_agent, state, "strategist")

def run_fact_checker(state: ResearchFlowState):
    return run_agent_with_metadata(factchecker_agent, state, "fact_checker")

def run_synthesizer(state: ResearchFlowState):
    return run_agent_with_metadata(synthesizer_agent, state, "synthesizer")

def run_reviewer(state: ResearchFlowState):
    return run_agent_with_metadata(reviewer_agent, state, "reviewer")


# Build the graph
graph = StateGraph(ResearchFlowState)

graph.add_node("clarifier", run_clarifier)
graph.add_node("decomposer", run_decomposer)
graph.add_node("strategist", run_strategist)
graph.add_node("researcher_hub", researcher_hub_graph)
graph.add_node("fact_checker", run_fact_checker)
graph.add_node("synthesizer", run_synthesizer)
graph.add_node("reviewer", run_reviewer)

# Define the flow
graph.set_entry_point("clarifier")
graph.add_edge("clarifier", "decomposer")
graph.add_edge("decomposer", "strategist")
graph.add_edge("strategist", "researcher_hub")
graph.add_edge("researcher_hub", "fact_checker")
graph.add_edge("fact_checker", "synthesizer")
graph.add_edge("synthesizer", "reviewer")
graph.add_edge("reviewer", END)

# Compile with metadata support
app_with_metadata = graph.compile()
