"""
Web search tools for the researcher agent.
Uses Tavily API with schema enforcement.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from tavily import TavilyClient

# Initialize Tavily client once
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

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
def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",
    include_raw_content: bool = True,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    time_range: Optional[Literal["day", "week", "month", "year"]] = None,
) -> Dict[str, Any]:
    """Run a Tavily web search and return raw JSON results."""
    args = SearchArgs(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
        include_raw_content=include_raw_content,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        time_range=time_range,
    )
    return tavily_client.search(**args.model_dump(exclude_none=True))

@tool
def tavily_extract(
    urls: List[str],
    extract_depth: Literal["basic", "advanced"] = "basic",
    format: Literal["markdown", "text"] = "markdown",
) -> Dict[str, Any]:
    """Extract full content from given URLs using Tavily."""
    args = ExtractArgs(urls=urls, extract_depth=extract_depth, format=format)
    return tavily_client.extract(**args.model_dump())

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
