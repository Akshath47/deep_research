"""
Scraper Node
Runs web searches for a subquery and saves raw results to files.
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from state import ResearchFlowState, read_json
from tools.web_search import (
    create_search_strategy,
    parse_search_results,
    format_search_content_for_storage,
    filter_results_by_score,
    rerank_results_by_source_type,
    SearchResult,
    SearchArgs,
)


def scraper_node(state: ResearchFlowState) -> Dict[str, Any]:
    """Main scraper node: search, filter, and save results."""
    subquery = state.get("current_subquery", {})
    idx = state.get("current_subquery_index", 0)
    if not subquery:
        return {"files": state.get("files", {})}

    # Build strategy from research plan
    plan = read_json(state, "research_plan.json", default={})
    strategy = create_search_strategy(plan, subquery)

    results, used_terms = [], []

    # Primary terms
    for term in strategy["primary_terms"]:
        r = _perform_search(term, strategy)
        if r:
            results.extend(r)
            used_terms.append(term)

    # Alternative terms if needed
    if len(results) < strategy.get("expected_sources", 5):
        for term in strategy.get("alternative_terms", []):
            r = _perform_search(term, strategy)
            if r:
                results.extend(r)
                used_terms.append(term)
            if len(results) >= strategy.get("expected_sources", 5):
                break

    # Dedup + filter
    results = _deduplicate_results(results)
    results = filter_results_by_score(results, min_score=0.2)

    # Boost sources if requested
    prefs = []
    if strategy.get("prefer_academic"): prefs.append("academic")
    if strategy.get("include_news"): prefs.append("news")
    if prefs: results = rerank_results_by_source_type(results, prefs)

    final = results[:strategy["max_results"]]
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
Strategy: {strategy.get('search_depth', 'basic')}
"""

    # Write summary file
    summary_file = f"raw_data/subquery{idx}_summary.txt"
    files[summary_file] = format_search_content_for_storage(final, subquery.get("query", ""), used_terms)

    # Metadata
    metadata = {
        "subquery_index": idx,
        "subquery_info": subquery,
        "search_terms_used": used_terms,
        "results_count": len(final),
        "search_strategy": strategy,
        "raw_data_files": [f"raw_data/subquery{idx}_result{i}.txt" for i in range(len(final))],
    }
    files[f"raw_data/subquery{idx}_metadata.json"] = json.dumps(metadata, indent=2)

    return {"files": files, "search_metadata": metadata}


def _perform_search(query: str, strategy: Dict[str, Any]) -> List[SearchResult]:
    """Run one Tavily search (placeholder until MCP is wired)."""
    try:
        args = SearchArgs(
            query=query,
            max_results=strategy.get("max_results", 5),
            search_depth=strategy.get("search_depth", "basic"),
            include_raw_content=True,
            include_domains=strategy.get("include_domains"),
            exclude_domains=strategy.get("exclude_domains"),
            time_range=strategy.get("time_range"),
        ).model_dump(exclude_none=True)
    except Exception as e:
        print("SearchArgs validation failed:", e)
        args = {"query": query, "max_results": 5, "search_depth": "basic", "include_raw_content": True}

    # TODO: integrate with MCP client
    # response = mcp_client.call("tavily-search", args)
    return []  # placeholder


def _deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results by URL."""
    seen, uniq = set(), []
    for r in results:
        if r.url not in seen:
            seen.add(r.url)
            uniq.append(r)
    return uniq
