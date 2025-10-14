import sys
import os
import json
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


# --- Generic Agent Runner ---

def run_agent(agent, state: ResearchFlowState):
    """
    Generic runner for all sub agents
    """
    result = agent.invoke(state)
    merged_files = {**state.get("files", {}), **result.get("files", {})}
    return {"files": merged_files}


# --- Individual Agent Runners ---

def run_clarifier(state: ResearchFlowState):
    return run_agent(clarifier_agent, state)


def run_decomposer(state: ResearchFlowState):
    return run_agent(decomposer_agent, state)


def run_strategist(state: ResearchFlowState):
    return run_agent(strategist_agent, state)


def run_fact_checker(state: ResearchFlowState):
    return run_agent(factchecker_agent, state)


def run_synthesizer(state: ResearchFlowState):
    return run_agent(synthesizer_agent, state)


def run_reviewer(state: ResearchFlowState):
    return run_agent(reviewer_agent, state)


# --- Map-Reduce for Researcher Hub ---

def map_each_subquery(state: ResearchFlowState):
    """
    Splits the clarified query into multiple subqueries for parallel research.
    Each subquery will spawn a new Researcher agent instance.
    
    Yields:
        Send: LangGraph Send objects for parallel execution
    """
    # Read subqueries from the virtual filesystem
    subqueries_content = state.get("files", {}).get("subqueries.json", "[]")
    try:
        subqueries = json.loads(subqueries_content)
    except json.JSONDecodeError:
        subqueries = []
    
    # Spawn a researcher for each subquery
    for idx, subq in enumerate(subqueries):
        yield Send("map_researcher", {"subquery": subq, "index": idx})


def run_researcher(state: ResearchFlowState):
    """
    Each researcher_agent handles one subquery.
    
    Args:
        state: ResearchFlowState containing subquery and index
        
    Returns:
        dict: Updated state with new files from this researcher
    """
    # Extract subquery and index from state
    subquery = state.get("subquery")
    index = state.get("index", 0)
    
    # Use deepcopy so parallel agents don't mutate shared state
    researcher_state = {
        "files": deepcopy(state.get("files", {})),
        "subquery": subquery,
        "index": index,
    }
    
    # Invoke the researcher agent (which is a CustomSubAgent with a subgraph)
    result = researcher_agent["graph"].invoke(researcher_state)
    
    return {"files": result.get("files", {})}


def run_researcher_merge(state: ResearchFlowState, inputs: list[dict]):
    """
    Merges all researcher outputs back into the main state.
    Uses DeepAgents' built-in file_reducer for consistency.
    
    Args:
        state: Current ResearchFlowState
        inputs: List of dicts from parallel researcher executions
        
    Returns:
        dict: Updated state with all merged files
    """
    merged_files = dict(state.get("files", {}))
    for inp in inputs:
        merged_files = file_reducer(merged_files, inp.get("files"))
    
    return {"files": merged_files}