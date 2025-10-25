"""
Researcher Hub - Map-Reduce pattern for parallel research execution.

This implements the parallel researcher execution.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.types import Send
from state import ResearchFlowState, ResearcherState, read_json
from agents.researcher import researcher_agent
from typing import Dict, Any, List


def map_each_subquery(state: ResearcherState):
    """
    Map function that spawns a researcher agent for each subquery.
    Needed for parallel execution of multiple research agents.
    """
    subqueries = read_json(state, "subqueries.json", default=[])
    sends = []
    for idx, subquery in enumerate(subqueries):
        # Send each subquery to a researcher agent instance
        send_data = {
            "current_subquery": subquery,
            "current_subquery_index": idx,
            "files": state.get("files", {}),
            "__metadata__": {"run_id": f"subquery_{idx}"}
        }        
        sends.append(Send("run_researcher", send_data))
    return sends


def map_subqueries_node(state: ResearcherState) -> Dict[str, Any]:
    """Dummy node that just passes state through (map happens via conditional edges)."""
    return {"files": state.get("files", {})}


def run_researcher(state: ResearcherState) -> Dict[str, Any]:
    """
    Run the researcher agent (CustomSubAgent with scraper → summarizer subgraph).
    """    
    result = researcher_agent["graph"].invoke(state)
    
    return {"files": result.get("files", {})}


def run_researcher_merge(state: ResearcherState) -> Dict[str, Any]:
    """
    Merge function that combines results from all researcher agents.
    """
    # The file_reducer in ResearchFlowState automatically merges files from parallel executions, so we just return the current state
    return {"files": state.get("files", {})}


def create_researcher_hub():
    """
    Create the researcher hub subgraph with map-reduce pattern.
    Uses ResearcherState to pass subquery information to researcher instances.
    """
    # Create the researcher hub subgraph using ResearcherState
    researcher_hub = StateGraph(ResearcherState)
    
    # Add map and reduce nodes
    researcher_hub.add_node("map_subqueries", map_subqueries_node)  # Dummy node for mapping
    researcher_hub.add_node("run_researcher", run_researcher)
    researcher_hub.add_node("merge_results", run_researcher_merge)
    
    # Set up map-reduce pattern
    researcher_hub.add_conditional_edges("map_subqueries", map_each_subquery, ["run_researcher"])
    researcher_hub.add_edge("run_researcher", "merge_results")
    
    # Set entry and exit points
    researcher_hub.set_entry_point("map_subqueries")
    researcher_hub.add_edge("merge_results", END)
    
    return researcher_hub.compile()


# Create the researcher hub instance
researcher_hub_graph = create_researcher_hub()