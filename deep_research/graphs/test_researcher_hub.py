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
        "executive_summary": "This research plan explores the recent developments and applications of agentic AI in the global finance sector, focusing on investment, trading, and banking. It also examines the benefits, challenges, and key players in the field. The plan prioritizes recent advancements and applications, followed by an analysis of benefits and challenges, and concludes with identifying leading companies and institutions.",
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
            {
                "id": 3,
                "query": "How is agentic AI being applied in the trading sector globally?",
                "priority": "high",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["agentic AI trading sector", "AI algorithmic trading", "AI market analysis trading"],
                "alternative_terms": ["AI trade execution", "AI trading strategies", "AI financial markets"],
                "max_results": 8,
                "search_depth": "advanced",
                "time_range": "year",
                "preferred_sources": ["academic", "web"],
                "include_domains": ["bloomberg.com", "reuters.com", "wsj.com"],
                "exclude_domains": [],
                "backup_strategy": "Focus on algorithmic trading if broader applications are limited"
                },
                "expected_results": 8,
                "dependencies": [],
                "can_run_parallel": True
            },
            {
                "id": 4,
                "query": "How is agentic AI being applied in the banking sector globally?",
                "priority": "high",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["agentic AI banking sector", "AI customer service banking", "AI fraud detection banking"],
                "alternative_terms": ["AI credit scoring banking", "AI banking operations", "AI financial services"],
                "max_results": 8,
                "search_depth": "advanced",
                "time_range": "year",
                "preferred_sources": ["academic", "web"],
                "include_domains": ["bankingtech.com", "forbes.com", "bloomberg.com"],
                "exclude_domains": [],
                "backup_strategy": "Focus on customer service applications if broader data is limited"
                },
                "expected_results": 8,
                "dependencies": [],
                "can_run_parallel": True
            },
            {
                "id": 5,
                "query": "What are the potential benefits and challenges of agentic AI applications in the finance sector?",
                "priority": "medium",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["agentic AI benefits finance", "AI challenges finance sector", "AI efficiency gains finance"],
                "alternative_terms": ["AI ethical concerns finance", "AI regulatory issues finance", "AI adoption finance"],
                "max_results": 6,
                "search_depth": "basic",
                "time_range": "year",
                "preferred_sources": ["news", "web"],
                "include_domains": ["forbes.com", "reuters.com", "financialtimes.com"],
                "exclude_domains": [],
                "backup_strategy": "Focus on specific challenges like ethical concerns if general data is sparse"
                },
                "expected_results": 6,
                "dependencies": [],
                "can_run_parallel": True
            },
            {
                "id": 6,
                "query": "Which companies or institutions are leading in agentic AI developments in the finance sector?",
                "priority": "medium",
                "freshness": "recent",
                "search_strategy": {
                "primary_terms": ["leading AI companies finance", "AI innovators finance sector", "AI leaders financial industry"],
                "alternative_terms": ["AI development finance companies", "AI pioneers finance", "AI institutions finance"],
                "max_results": 6,
                "search_depth": "basic",
                "time_range": "year",
                "preferred_sources": ["news", "web"],
                "include_domains": ["crunchbase.com", "forbes.com", "bloomberg.com"],
                "exclude_domains": [],
                "backup_strategy": "Focus on major tech companies if specific finance sector leaders are limited"
                },
                "expected_results": 6,
                "dependencies": [],
                "can_run_parallel": True
            }
            ],
            "execution_order": [1, 2, 3, 4, 5, 6],
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
        {
            "id": 3,
            "query": "How is agentic AI being applied in the trading sector globally?",
            "priority": "high",
            "freshness": "recent",
            "description": "This sub-query investigates the role of agentic AI in trading activities, such as algorithmic trading, market analysis, and trade execution."
        },
        {
            "id": 4,
            "query": "How is agentic AI being applied in the banking sector globally?",
            "priority": "high",
            "freshness": "recent",
            "description": "This sub-query examines the integration and impact of agentic AI in banking operations, including customer service, fraud detection, and credit scoring."
        },
        {
            "id": 5,
            "query": "What are the potential benefits and challenges of agentic AI applications in the finance sector?",
            "priority": "medium",
            "freshness": "recent",
            "description": "This sub-query analyzes the advantages and potential obstacles associated with the adoption of agentic AI in finance, such as efficiency gains, ethical concerns, and regulatory issues."
        },
        {
            "id": 6,
            "query": "Which companies or institutions are leading in agentic AI developments in the finance sector?",
            "priority": "medium",
            "freshness": "recent",
            "description": "This sub-query identifies key players and innovators in the field of agentic AI within the finance sector, highlighting their contributions and influence."
        }
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