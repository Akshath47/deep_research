"""
Scraper Node
Uses an LLM with Tavily tools to run searches for a subquery and save raw results.
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from state import ResearcherState
from tools.web_search import (
    tavily_search,
    tavily_extract,
    parse_search_results,
    format_search_content_for_storage,
    filter_results_by_score,
    rerank_results_by_source_type,
    SearchResult,
)
from deep_research.config.models import get_model
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, ValidationError
from utils.prompts import SCRAPER_PROMPT

# --- Structured schema for scraper final output (what the LLM must return) ---

class TavilyResult(BaseModel):
    url: str
    title: str
    snippet: str
    content: str
    published_date: Optional[str] = None
    score: float

class ScraperOutput(BaseModel):
    results: List[TavilyResult]
    terms_used: List[str]

# Use ReAct agent pattern to allow the LLM to decide when to use which tool and validate outputs and reiterate if needed
llm = get_model("scraper_node")
_scraper_node_agent = create_react_agent(
    llm,
    tools=[tavily_search, tavily_extract],
)

def scraper_node(state: ResearcherState) -> Dict[str, Any]:
    """Scraper node: run Tavily via LLM, process results, and save to files."""    
    subquery = state.get("current_subquery", {})
    idx = state.get("current_subquery_index", 0)
    if not subquery:
        return {"files": state.get("files", {})}

    # Ask LLM (via ReAct) to search/extract until it has good results; return ScraperOutput
    prompt = f"{SCRAPER_PROMPT}\n\nSubquery: {subquery.get('query', '')}"
    # ReAct agent expects a state dict with messages, not a list
    llm_res = _scraper_node_agent.invoke({"messages": [HumanMessage(content=prompt)]})

    # ReAct agent returns a dict. Its "output" should be ScraperOutput (pydantic) or a dict matching it.
    raw_out = llm_res.get("output", {})

    # Validate output schema to ensure it matches ScraperOutput and can be used by tavily parsers
    try:
        out = ScraperOutput.model_validate(raw_out).model_dump()
    except ValidationError as e:
        print("Schema validation failed:", e)
        out = {"results": [], "terms_used": [subquery.get("query", "")]}

    # Normalize into SearchResult objects
    results = parse_search_results({"results": out.get("results", [])})
    used_terms = out.get("terms_used") or [subquery.get("query", "")]

    # Dedup + filter
    results = _deduplicate_results(results)
    results = filter_results_by_score(results, min_score=0.2)

    # Optional boosts based on subquery hints
    prefs = []
    if subquery.get("prefer_academic"): prefs.append("academic")
    if subquery.get("include_news"):    prefs.append("news")
    if prefs: results = rerank_results_by_source_type(results, prefs)

    final = results[:5]
    files = dict(state.get("files", {}))

    # Write per-result files
    for i, r in enumerate(final):
        fname = f"raw_data/subquery{idx}_result{i}.txt"
        files[fname] = f"""# Raw Search Result {i+1}

URL: {r.url}
Title: {r.title}
Type: {r.source_type}
Published: {r.published_date or 'Unknown'}
Score: {r.score}

Content:
{r.content}

Snippet:
{r.snippet}

---
Search Terms: {', '.join(used_terms)}
Subquery: {subquery.get('query', '')}
"""

    # Summary file for the subquery
    summary_file = f"raw_data/subquery{idx}_summary.txt"
    files[summary_file] = format_search_content_for_storage(final, subquery.get("query", ""), used_terms)

    # Metadata for downstream nodes
    metadata = {
        "subquery_index": idx,
        "subquery_info": subquery,
        "search_terms_used": used_terms,
        "results_count": len(final),
        "raw_data_files": [f"raw_data/subquery{idx}_result{i}.txt" for i in range(len(final))],
    }
    files[f"raw_data/subquery{idx}_metadata.json"] = json.dumps(metadata, indent=2)

    return {"files": files, "search_metadata": metadata}


def _deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results by URL."""
    seen, uniq = set(), []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            uniq.append(r)
    return uniq
