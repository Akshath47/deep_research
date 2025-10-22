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
from graphs.researcher_hub import researcher_hub_graph


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



# --- Build the Graph Workflow ---

graph = StateGraph(ResearchFlowState)

graph.add_node("clarifier", run_clarifier)
graph.add_node("decomposer", run_decomposer)
graph.add_node("strategist", run_strategist)

# Use the researcher hub subgraph from researcher_hub.py
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

# Compile main graph
app = graph.compile()