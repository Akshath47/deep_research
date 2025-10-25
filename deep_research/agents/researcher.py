"""
Researcher Agent for Deep Research Multi-Agent System

This agent is implemented as a CustomSubAgent with a LangGraph subgraph
containing two sequential nodes: scraper → summarizer.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from state import ResearcherState
from nodes.scraper_node import scraper_node
from nodes.summarizer_node import summarizer_node
from deepagents.sub_agent import CustomSubAgent

def create_researcher_subgraph():
    """
    Create the researcher subgraph with two sequential nodes.
    This provides guaranteed sequential execution: scraper → summarizer
    
    Uses ResearcherState which includes current_subquery and current_subquery_index
    fields needed for parallel execution.
    """
    # Create the subgraph using ResearcherState
    researcher_graph = StateGraph(ResearcherState)
    
    # Add the two sequential nodes
    researcher_graph.add_node("scraper", scraper_node)
    researcher_graph.add_node("summarizer", summarizer_node)
    
    # Define the sequential flow: scraper → summarizer
    researcher_graph.add_edge("scraper", "summarizer")
    
    # Set entry and exit points
    researcher_graph.set_entry_point("scraper")
    researcher_graph.add_edge("summarizer", END)
    
    # Compile the graph
    return researcher_graph.compile()


def create_researcher_custom_agent() -> CustomSubAgent:
    """
    Create the researcher as a CustomSubAgent for integration with deepagents.
    """
    researcher_custom_agent: CustomSubAgent = {
        "name": "researcher",
        "description": "Execute research by scraping web sources and creating LLM-powered summaries with citations",
        "graph": create_researcher_subgraph()
    }
    
    return researcher_custom_agent


# Create the researcher agent instance
researcher_agent = create_researcher_custom_agent()