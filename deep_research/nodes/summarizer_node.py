"""
Summarizer Node
Reads raw search results and creates structured summaries using LLM.
"""

import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from state import ResearchFlowState, read_text, read_json
from deepagents.model import get_default_model
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from datetime import datetime


# Schema for structured LLM output
class SummaryAnalysis(BaseModel):
    key_findings: List[str]
    main_arguments: List[str]
    data_points: List[str]
    conclusions: List[str]
    relevance_to_query: str
    source_reliability: str
    summary_text: str
    extracted_url: str
    extracted_title: str


def summarizer_node(state: ResearchFlowState) -> Dict[str, Any]:
    """Summarize raw data files into structured JSON summaries."""
    meta = state.get("search_metadata", {})
    idx = meta.get("subquery_index", 0)
    subquery = meta.get("subquery_info", {})

    if not meta or not meta.get("raw_data_files"):
        return {"files": state.get("files", {})}

    files = dict(state.get("files", {}))
    llm = get_default_model()
    summaries = []

    for i, raw_path in enumerate(meta["raw_data_files"]):
        raw = read_text(state, raw_path, default="")
        if not raw:
            print(f"Skipped empty file {raw_path}")
            continue

        summary = _create_llm_summary(llm, raw, subquery, i)
        fname = f"summaries/subquery{idx}_result{i}.json"
        files[fname] = json.dumps(summary, indent=2)
        summaries.append(summary)

    # Index file for this subquery
    index_data = {
        "subquery_index": idx,
        "subquery": subquery.get("query", ""),
        "priority": subquery.get("priority", "medium"),
        "freshness": subquery.get("freshness", "any"),
        "summaries_count": len(summaries),
        "summary_files": [f"summaries/subquery{idx}_result{i}.json" for i in range(len(summaries))],
        "summaries": summaries,
    }
    index_file = f"summaries/subquery{idx}_index.json"
    files[index_file] = json.dumps(index_data, indent=2)

    return {"files": files, "summary_files": index_data["summary_files"], "summary_index": index_file}


def _create_llm_summary(llm, raw: str, subquery: Dict[str, Any], i: int) -> Dict[str, Any]:
    """Ask LLM to analyze one raw search result."""
    q = subquery.get("query", "")
    prompt = f"""Analyze this search result for the research question below.

Research Question: {q}

Raw Content:
{raw}

Return key findings, arguments, data, conclusions, relevance, reliability, and a short summary.
Also extract the URL and title if present."""

    structured_llm = llm.with_structured_output(SummaryAnalysis)
    analysis = structured_llm.invoke([HumanMessage(content=prompt)])

    return {
        "result_index": i,
        "subquery": q,
        "llm_analysis": analysis.model_dump(),
        "citation": f"[Source: {analysis.extracted_url}]",
        "generated_at": datetime.utcnow().isoformat(),
    }
