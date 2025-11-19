"""
Researcher Hub - Map-Reduce pattern for parallel research execution.

This implements the parallel researcher execution.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from state import ResearchFlowState, ResearcherState, read_json
from agents.researcher import researcher_agent
from typing import Dict, Any, List

# Semaphore to limit concurrent researcher executions to 2
_researcher_semaphore = threading.Semaphore(2)


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
    Uses semaphore to limit concurrent executions to 2.
    """
    import traceback
    
    subquery_idx = state.get("current_subquery_index", "unknown")
    subquery = state.get("current_subquery", {})
    query_text = subquery.get("query", "unknown") if isinstance(subquery, dict) else str(subquery)
    
    print(f"[RESEARCHER HUB] Starting researcher for subquery {subquery_idx}: {query_text[:50]}...")
    
    _researcher_semaphore.acquire()
    try:
        result = researcher_agent["graph"].invoke(state)
        print(f"[RESEARCHER HUB] ✓ Subquery {subquery_idx} completed successfully")
        return {"files": result.get("files", {})}
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[RESEARCHER HUB] ✗ Subquery {subquery_idx} FAILED with {error_type}: {error_msg}")
        print(f"[RESEARCHER HUB] Traceback:\n{traceback.format_exc()}")
        
        # Create error file instead of crashing
        files = state.get("files", {})
        files[f"errors/subquery{subquery_idx}_error.txt"] = f"""# Research Error
        
Subquery: {query_text}
Error Type: {error_type}
Error Message: {error_msg}

Traceback:
{traceback.format_exc()}

This subquery failed but other researchers continued.
"""
        print(f"[RESEARCHER HUB] Returning partial results for subquery {subquery_idx}")
        return {"files": files}
    finally:
        _researcher_semaphore.release()


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