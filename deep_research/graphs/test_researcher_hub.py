"""
Test graph for researcher hub in isolation.
This allows testing the researcher hub subgraph independently with pre-built input state.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from langgraph.graph import StateGraph, END
from state import ResearchFlowState
from graphs.researcher_hub import researcher_hub_graph


def initialize_test_state(state: ResearchFlowState):
    """
    Initialize test state with template files that the researcher hub expects.
    The researcher hub needs:
    - clarified_query.md: The clarified user query
    - research_plan.json: The research strategy and plan
    - subqueries.json: List of research subqueries to investigate
    """
    # Initialize the virtual filesystem with template files
    files = state.get("files", {})
    
    # Template 1: clarified_query.md
    files["clarified_query.md"] = """#Clarified Research Query

Original Query
Research about the effects of agentic ai developments in the finance sector

Clarifications Received
The user is interested in a global overview of agentic AI developments in the finance sector, focusing on areas like investments, trading, and banks, over the past year.

Refined Research Objective
Analyze the effects of agentic AI developments in the global finance sector over the past year.

Research Scope and Boundaries
Global, focusing on investments, trading, and banking sectors.

Key Questions to Answer
What are the recent developments in agentic AI within the finance sector?
How is agentic AI being applied in investments, trading, and banking?
What are the potential benefits and challenges of these AI applications?
Which companies or institutions are leading in these developments?

Constraints and Requirements
Focus on developments from the past year.

Expected Deliverable Format
comprehensive research report

Research Brief Summary
This research will focus on: Analyze the effects of agentic AI developments in the global finance sector over the past year.
The research scope includes: Global, focusing on investments, trading, and banking sectors.
The final deliverable will be: comprehensive research report
"""
    
    # Template 2: research_plan.json
    files["research_plan.json"] = json.dumps({
        "executive_summary": "This research plan explores the recent developments and applications of agentic AI in the global finance sector, focusing on investment and trading. The plan prioritizes recent advancements and their applications in these key areas.",
        "subqueries": [
            {
                "id": 1,
                "query": "What are the recent developments in agentic AI within the global finance sector over the past year?",
                "priority": "high",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["agentic AI finance 2023", "AI innovations finance sector", "latest AI developments finance"],
                "alternative_terms": ["AI advancements financial industry", "new AI technologies finance 2023", "AI trends finance sector"],
                "max_results": 10,
                "search_depth": "advanced",
                "time_range": "year",
                "preferred_sources": ["academic", "news", "web"],
                "include_domains": ["forbes.com", "bloomberg.com", "reuters.com"],
                "exclude_domains": [],
                "backup_strategy": "Expand search to include related AI technologies if specific agentic AI data is limited"
                },
                "expected_results": 10,
                "dependencies": [],
                "can_run_parallel": True
            },
            {
                "id": 2,
                "query": "How is agentic AI being applied in the investment sector globally?",
                "priority": "high",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["agentic AI investment sector", "AI portfolio management", "AI risk assessment investment"],
                "alternative_terms": ["AI decision-making investment", "AI investment strategies", "AI financial analysis"],
                "max_results": 8,
                "search_depth": "advanced",
                "time_range": "year",
                "preferred_sources": ["academic", "web"],
                "include_domains": ["investopedia.com", "bloomberg.com", "financialtimes.com"],
                "exclude_domains": [],
                "backup_strategy": "Focus on specific AI applications like portfolio management if general data is sparse"
                },
                "expected_results": 8,
                "dependencies": [],
                "can_run_parallel": True
            },
            ],
            "execution_order": [1, 2],
            "quality_criteria": [
            "Prioritize peer-reviewed publications and reputable news sources",
            "Use sources published within the last year for currency",
            "Ensure global coverage with a focus on major financial markets",
            "Validate claims with multiple authoritative sources"
            ]
    }, indent=2)
    
    # Template 3: subqueries.json
    files["subqueries.json"] = json.dumps([
        {
            "id": 1,
            "query": "What are the recent developments in agentic AI within the global finance sector over the past year?",
            "priority": "high",
            "freshness": "recent",
            "description": "This sub-query focuses on identifying and summarizing the latest advancements and innovations in agentic AI technologies as applied to the finance sector globally."
        },
        {
            "id": 2,
            "query": "How is agentic AI being applied in the investment sector globally?",
            "priority": "high",
            "freshness": "recent",
            "description": "This sub-query explores the specific applications and use cases of agentic AI in the investment sector, including portfolio management, risk assessment, and decision-making processes."
        },
    ], indent=2)
    
    return {"files": files}


# Build test graph
test_graph = StateGraph(ResearchFlowState)

# Add initialization node
test_graph.add_node("initialize", initialize_test_state)

# Add the researcher hub as a node
test_graph.add_node("researcher_hub", researcher_hub_graph)

# Add a final node to verify results
def verify_results(state: ResearchFlowState):
    """Show what files were created by the researcher hub"""
    files = state.get("files", {})
    print("\n=== Researcher Hub Output Files ===")
    for path in sorted(files.keys()):
        print(f"  - {path}")
    return {"files": files}

test_graph.add_node("verify", verify_results)

# Connect the nodes
test_graph.set_entry_point("initialize")
test_graph.add_edge("initialize", "researcher_hub")
test_graph.add_edge("researcher_hub", "verify")
test_graph.add_edge("verify", END)

# Compile the test graph
app = test_graph.compile()