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
from config.models import get_model
from langchain.agents import create_agent
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
_scraper_node_agent = create_agent(
    model=llm,
    tools=[tavily_search, tavily_extract],
)

def scraper_node(state: ResearcherState) -> Dict[str, Any]:
    """Scraper node: run Tavily via LLM, process results, and save to files."""
    import traceback
    
    subquery = state.get("current_subquery", {})
    idx = state.get("current_subquery_index", 0)
    if not subquery:
        return {"files": state.get("files", {})}

    query_text = subquery.get('query', '')
    print(f"[SCRAPER NODE] Starting scrape for subquery {idx}: {query_text[:50]}...")

    try:
        # Step 1: Use ReAct agent to call Tavily tools and gather information
        prompt = f"{SCRAPER_PROMPT}\n\nSubquery: {query_text}"

        # CRITICAL: Limit recursion to prevent token explosion
        # Most searches should complete in 5-8 tool calls max
        from langchain_core.runnables.config import RunnableConfig
        config = RunnableConfig(recursion_limit=10)

        llm_res = _scraper_node_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config
        )
        messages = llm_res.get("messages", [])
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[SCRAPER NODE] ✗ Tool execution failed for subquery {idx}: {error_type}: {error_msg}")
        
        # Return empty results with error metadata instead of crashing
        files = state.get("files", {})
        files[f"raw_data/subquery{idx}_error.txt"] = f"""# Scraper Error

Subquery: {query_text}
Error Type: {error_type}
Error Message: {error_msg}

This search failed but processing continues with empty results.
"""
        return {
            "files": files,
            "search_metadata": {
                "subquery_index": idx,
                "subquery_info": subquery,
                "search_terms_used": [query_text],
                "results_count": 0,
                "raw_data_files": [],
                "error": error_msg
            }
        }
    
    # DEBUG: Log message count and approximate token usage
    total_chars = sum(len(str(msg.content)) for msg in messages if hasattr(msg, 'content'))
    print(f"[SCRAPER DEBUG] ReAct agent returned {len(messages)} messages, ~{total_chars} chars (~{total_chars//4} tokens)")

    # Step 2: Extract tool results from messages and structure them with a second LLM call
    # CRITICAL FIX: Don't pass full messages (351k tokens!), extract only essential data
    
    tool_results_summary = _extract_tool_results_summary(messages)
    print(f"[SCRAPER DEBUG] Extracted tool results: {len(tool_results_summary)} chars (~{len(tool_results_summary)//4} tokens)")
    
    # Build a concise prompt with just the extracted data
    extraction_prompt = f"""Based on these search results, extract and structure the information.

Original subquery: {subquery.get('query', '')}

Tool Results:
{tool_results_summary}

Create a structured output with:
- A list of the best 5-8 search results (URL, title, snippet, content, published date if available, and relevance score)
- The search terms that were actually used

Focus on the most relevant, high-quality results."""

    # Use structured output to get ScraperOutput
    structured_llm = llm.with_structured_output(ScraperOutput)
    
    try:
        # Pass only the minimal context, not the entire conversation history
        scraper_output = structured_llm.invoke([HumanMessage(content=extraction_prompt)])
        out = scraper_output.model_dump()
        print(f"[SCRAPER NODE] ✓ Successfully structured {len(out.get('results', []))} results for subquery {idx}")
    except (ValidationError, Exception) as e:
        print(f"[SCRAPER NODE] Warning: Failed to structure scraper output for subquery {idx}: {e}")
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


def _extract_tool_results_summary(messages: List) -> str:
    """
    Extract a concise summary of tool call results from the message history.
    This prevents sending 351k+ tokens to the LLM by extracting only key metadata.
    """
    from langchain_core.messages import ToolMessage
    
    summaries = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                # Parse the tool result
                content = msg.content
                if isinstance(content, str):
                    import json
                    data = json.loads(content)
                else:
                    data = content
                
                # Extract just the key fields, not full content
                if "results" in data:
                    for result in data.get("results", [])[:10]:  # Limit to 10 results
                        summary = {
                            "url": result.get("url", ""),
                            "title": result.get("title", "")[:200],  # Truncate title
                            "snippet": result.get("snippet", "")[:500],  # Truncate snippet
                            "score": result.get("score", 0.0),
                            "published_date": result.get("published_date"),
                        }
                        # Only include first 1000 chars of content to stay within limits
                        if "content" in result:
                            summary["content"] = result["content"][:1000] + "..."
                        summaries.append(json.dumps(summary))
            except Exception as e:
                print(f"Warning: Failed to parse tool message: {e}")
                continue
    
    return "\n\n".join(summaries) if summaries else "No tool results found"


def _deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results by URL."""
    seen, uniq = set(), []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            uniq.append(r)
    return uniq
