"""
Web search tools for the researcher agent.
Uses Tavily MCP server with schema enforcement.
"""

import sys, os, re, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional, Literal, cast
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- Schemas ---

class SearchArgs(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=5, le=20)
    search_depth: Literal["basic", "advanced"] = "basic"
    include_raw_content: bool = True
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    time_range: Optional[Literal["day", "week", "month", "year"]] = None

class ExtractArgs(BaseModel):
    urls: List[str]
    extract_depth: Literal["basic", "advanced"] = "basic"
    format: Literal["markdown", "text"] = "markdown"

class SearchResult(BaseModel):
    url: str
    title: str
    content: str
    snippet: str
    published_date: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)
    source_type: str = "web"

# --- Tools ---

@tool
def prepare_tavily_search_args(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",
    include_raw_content: bool = True,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    time_range: Optional[Literal["day", "week", "month", "year"]] = None
) -> Dict[str, Any]:
    """Validate and prepare search args."""
    try:
        args = SearchArgs(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=include_raw_content,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            time_range=time_range
        )
        return {k: v for k, v in args.model_dump().items() if v is not None}
    except Exception as e:
        print("SearchArgs validation failed:", e)
        return {"query": query, "max_results": 5, "search_depth": "basic", "include_raw_content": True}

@tool
def prepare_tavily_extract_args(
    urls: List[str],
    extract_depth: str = "basic",
    format: str = "markdown"
) -> Dict[str, Any]:
    """Validate and prepare extract args."""
    try:
        depth = cast(
            Literal["basic", "advanced"],
            extract_depth if extract_depth in ["basic", "advanced"] else "basic"
        )
        fmt = cast(
            Literal["markdown", "text"],
            format if format in ["markdown", "text"] else "markdown"
        )
        return ExtractArgs(urls=urls, extract_depth=depth, format=fmt).model_dump()
    except Exception as e:
        print("ExtractArgs validation failed:", e)
        return {"urls": urls, "extract_depth": "basic", "format": "markdown"}

# --- Utils ---

def parse_search_results(search_response: Dict[str, Any]) -> List[SearchResult]:
    """Convert Tavily results into normalized SearchResult objects."""
    results = search_response.get("results", []) or []
    if not results:
        return []

    scores = [r.get("score", 0.0) for r in results if r.get("score") is not None]
    min_s, max_s = (min(scores), max(scores)) if scores else (0.0, 1.0)
    rng = max_s - min_s if max_s > min_s else 1.0

    parsed = []
    for r in results:
        raw = r.get("score", 0.0)
        norm = (raw - min_s) / rng if rng > 0 else 0.0
        url = r.get("url", "")
        stype = "web"
        if any(k in url for k in ["news", "reuters", "cnn", "bbc", "ap"]):
            stype = "news"
        elif any(k in url for k in ["pubmed", "arxiv", "scholar", "doi"]):
            stype = "academic"
        parsed.append(SearchResult(
            url=url,
            title=r.get("title", ""),
            content=r.get("content", ""),
            snippet=r.get("snippet", ""),
            published_date=r.get("published_date"),
            score=round(norm, 3),
            source_type=stype
        ))
    return sorted(parsed, key=lambda x: x.score, reverse=True)

def format_search_content_for_storage(results: List[SearchResult], subquery: str, terms: List[str]) -> str:
    """Format results into plain text for storage."""
    out = f"# Raw Search Results\n\n## Subquery\n{subquery}\n\n## Search Terms\n{', '.join(terms)}\n\n"
    for i, r in enumerate(results, 1):
        out += f"""### Result {i}: {r.title}
URL: {r.url}
Type: {r.source_type}
Published: {r.published_date or 'Unknown'}
Score: {r.score}

Content:
{r.content}

Snippet:
{r.snippet}

---
"""
    return out

def extract_urls_from_results(results: List[SearchResult]) -> List[str]:
    """Get URLs from results."""
    return [r.url for r in results if r.url]

def filter_results_by_score(results: List[SearchResult], min_score: float = 0.3) -> List[SearchResult]:
    """Filter results above score threshold."""
    return [r for r in results if r.score >= min_score]

def rerank_results_by_source_type(results: List[SearchResult], preferred: Optional[List[str]] = None) -> List[SearchResult]:
    """Boost scores for preferred source types."""
    if not preferred:
        return results
    boosted = []
    for r in results:
        s = min(1.0, r.score * 1.2) if r.source_type in preferred else r.score
        boosted.append(r.copy(update={"score": s}))
    return sorted(boosted, key=lambda x: x.score, reverse=True)

def create_search_strategy(plan: Dict[str, Any], subquery_info: Dict[str, Any]) -> Dict[str, Any]:
    """Pick search strategy for a subquery from the research plan, or fallback."""
    sid = subquery_info.get("id", 1)
    sq = next((s for s in plan.get("subqueries", []) if s.get("id") == sid), None)
    if not sq:
        return _fallback_strategy(subquery_info)

    strat = sq.get("search_strategy", {})
    return {
        "primary_terms": strat.get("primary_terms", [subquery_info.get("query", "")]),
        "alternative_terms": strat.get("alternative_terms", []),
        "max_results": strat.get("max_results", 5),
        "search_depth": strat.get("search_depth", "basic"),
        "include_raw_content": True,
        "time_range": strat.get("time_range"),
        "preferred_sources": strat.get("preferred_sources", ["web"]),
        "include_domains": strat.get("include_domains", []),
        "exclude_domains": strat.get("exclude_domains", []),
        "backup_strategy": strat.get("backup_strategy", "Expand if limited"),
        "expected_sources": sq.get("expected_results", 5),
        "can_run_parallel": sq.get("can_run_parallel", True),
        "dependencies": sq.get("dependencies", [])
    }

def _fallback_strategy(subquery_info: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback strategy if not found in plan."""
    q = subquery_info.get("query", "")
    pri = subquery_info.get("priority", "medium")
    fresh = subquery_info.get("freshness", "any")
    return {
        "primary_terms": _generate_terms(q),
        "alternative_terms": [],
        "max_results": 8 if pri == "high" else 5,
        "search_depth": "advanced" if pri == "high" else "basic",
        "include_raw_content": True,
        "time_range": "month" if fresh == "recent" else None,
        "preferred_sources": ["web"],
        "include_domains": [],
        "exclude_domains": [],
        "backup_strategy": "Expand if limited",
        "expected_sources": 5,
        "can_run_parallel": True,
        "dependencies": []
    }

def _generate_terms(query: str) -> List[str]:
    """Make simple variations of a query."""
    q = query.lower()
    terms = [query]
    if q.startswith("what are") or q.startswith("what is"):
        terms.append(re.sub(r'^what (are|is)\s+', '', q))
    if q.startswith("how "):
        terms.append(re.sub(r'^how\s+', '', q))
    if len(query.split()) > 2:
        terms.append(f'"{query}"')
    return terms[:3]
