# 📝 Deep Research Multi-Agent (v1) Plan

## Overview
We are building a multi-agent research system with **one orchestrator** and a team of **specialized sub-agents**.  
- All agents share a **virtual filesystem** (`DeepAgentState.files`).  
- Files are just key–value entries in memory (`{filename: content}`).  
- Each agent writes its outputs to well-defined filenames so that downstream agents can pick them up.  
- Parallelism is applied in the **Researcher stage** — multiple research agents are spawned simultaneously, each working on a different sub-query.

---

## 🔹 Agents

### 1. **Clarifier Agent**
- **Role**: Ask the user clarifying questions and refine the original query into a crystal-clear research brief.  
- **Reads**: User input.  
- **Writes**: `clarified_query.md` → refined, unambiguous version of the query.  
- **Flow**: Sequential (first step).  

---

### 2. **Decomposer Agent**
- **Role**: Break down the clarified query into smaller, focused sub-queries.  
- **Reads**: `clarified_query.md`.  
- **Writes**: `subqueries.json` → structured list of sub-queries with optional metadata (priority, freshness).  
- **Flow**: Sequential.  

---

### 3. **Strategist Agent**
- **Role**: Design the research plan.  
  - Expand sub-queries into multiple search phrases.  
  - Suggest order of execution.  
  - Specify tools (news, general search, finance, etc.).  
- **Reads**: `subqueries.json`.  
- **Writes**: `research_plan.md` → prioritized plan with search terms.  
- **Flow**: Sequential.  

---

### 4. **Researcher Agent (multi-step subgraph)**
- **Role**: Execute research plan by scraping + summarizing.  
- **Architecture**: This agent is a *subgraph with two sequential steps*:
  1. **Scraping Node**  
     - Perform web search and scrape top results.  
     - Write raw text to `/raw_data/subqueryX_resultY.txt`.  
  2. **Summarizing Node**  
     - Write short digest of each source, with explicit citation.  
     - Save to `/summaries/subqueryX_resultY.md`.  
     - Always include `[Source: <URL>]`.  
- **Reads**: `research_plan.md`.  
- **Writes**:  
  - `/raw_data/*` → full scraped content.  
  - `/summaries/*` → compressed digest with citation.  
- **Flow**: **Parallel**. Multiple Researcher Agents are spawned — one per sub-query (or even per search result).

---

### 5. **Fact-Checker Agent**
- **Role**: Cross-check facts, detect contradictions, and filter out unreliable claims.  
- **Reads**: `/summaries/*`, `/raw_data/*`.  
- **Writes**: `factcheck_notes.md` → list of verified claims, contradictions, flagged weak sources.  
- **Flow**: Sequential (runs after Researcher outputs are gathered).  

---

### 6. **Synthesizer Agent**
- **Role**: Write a draft report in academic style.  
- **Reads**:  
  - `clarified_query.md` (for context of main question).  
  - `/summaries/*` (primary material).  
  - `factcheck_notes.md` (validated facts).  
  - `/raw_data/*` (fallback, if needed).  
- **Writes**: `draft_report.md` → structured paper with inline citations `[1], [2], ...`.  
- **Flow**: Sequential.  

---

### 7. **Reviewer Agent** (merged reflector + refiner)
- **Role**: Final polish + gap detection.  
  - Ensure draft covers all sub-queries.  
  - Check completeness and clarity.  
  - Fill minor gaps directly into the report.  
  - Write a gap log for future refinement cycles.  
- **Reads**:  
  - `draft_report.md`.  
  - `subqueries.json`.  
- **Writes**:  
  - `final_paper.md`.  
  - `gap_list.json` (not acted on yet in v1).  
- **Flow**: Sequential (final stage).  

---

## 🔹 Graph Flow

```mermaid
graph TD
    UserQuery[User Query] --> Clarifier
    Clarifier -->|clarified_query.md| Decomposer
    Decomposer -->|subqueries.json| Strategist
    Strategist -->|research_plan.md| ResearcherHub

    subgraph ResearcherHub
        direction LR
        R1[Researcher Sub-Agent 1\n(scrape + summarize)]
        R2[Researcher Sub-Agent 2\n(scrape + summarize)]
        R3[Researcher Sub-Agent 3\n(scrape + summarize)]
    end

    ResearcherHub -->|/summaries/* + /raw_data/*| FactChecker
    FactChecker -->|factcheck_notes.md| Synthesizer
    Synthesizer -->|draft_report.md| Reviewer
    Reviewer -->|final_paper.md + gap_list.json| UserOutput[Final Output]


## 🔹 Coding Plan

# --- 1. Define the State ---
class ResearchFlowState(DeepAgentState):
    files: dict[str, str] = {}

    .. anything else that is needed


# --- 2. Agents ---
# (clarifier_agent, decomposer_agent, strategist_agent,
#  researcher_agent, factchecker_agent, synthesizer_agent, reviewer_agent)
# ... same as before ...


# --- 3. Node Runners ---

def run_agent(agent, state: ResearchFlowState):
    """
    Generic runner for any DeepAgent-based node.
    Invokes the agent, merges returned files with the existing state,
    and returns the updated state in LangGraph-compatible format.
    """
    result = agent.invoke(state)
    merged_files = {**state.files, **result.get("files", {})}
    return {"files": merged_files}


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


# --- 4. Map–Reduce for ResearcherHub ---
from copy import deepcopy
from langgraph.graph import Send


def map_each_subquery(state: ResearchFlowState):
    """
    Splits the clarified query into multiple subqueries for parallel research.
    Each subquery will spawn a new Researcher agent instance.
    """
    subqueries = state.read_json("subqueries.json") or []
    for idx, subq in enumerate(subqueries):
        yield Send("map_researcher", {"subquery": subq, "index": idx})


def run_researcher(state: ResearchFlowState, subquery: dict, index: int):
    """
    Each researcher_agent handles one subquery.
    It should fetch multiple results and name files consistently:
      /raw_data/subquery{index}_result{k}.txt
      /summaries/subquery{index}_result{k}.md
    """
    # Use deepcopy so parallel agents don’t mutate shared state
    result = researcher_agent.invoke({
        "files": deepcopy(state.files),
        "subquery": subquery,
        "index": index,
    })

    return {"files": result.get("files", {})}

from deepagents.state import file_reducer

def run_researcher_merge(state: ResearchFlowState, inputs: list[dict]):
    """
    Merges all researcher outputs back into the main state.
    Uses DeepAgents' built-in file_reducer for consistency.
    (This applies a last-write-wins merge for duplicate file paths.)
    """
    merged_files = dict(state.files)
    for inp in inputs:
        merged_files = file_reducer(merged_files, inp.get("files"))

    return {"files": merged_files}



# --- 5. Build Graph ---
workflow = StatefulGraph(ResearchFlowState)

workflow.add_node("clarifier", run_clarifier)
workflow.add_node("decomposer", run_decomposer)
workflow.add_node("strategist", run_strategist)

# ResearcherHub as subgraph
researcher_hub = workflow.add_subgraph("researcher_hub")
researcher_hub.add_node("map_researcher", run_researcher)
researcher_hub.add_node("reduce_researcher", run_researcher_merge)
researcher_hub.add_conditional_edges("map_researcher", map_each_subquery)
researcher_hub.add_edge("map_researcher", "reduce_researcher")

workflow.add_node("fact_checker", run_fact_checker)
workflow.add_node("synthesizer", run_synthesizer)
workflow.add_node("reviewer", run_reviewer)

# --- 6. Define Flow ---
workflow.set_entry_point("clarifier")
workflow.add_edge("clarifier", "decomposer")
workflow.add_edge("decomposer", "strategist")
workflow.add_edge("strategist", "researcher_hub")
workflow.add_edge("researcher_hub", "fact_checker")
workflow.add_edge("fact_checker", "synthesizer")
workflow.add_edge("synthesizer", "reviewer")
workflow.add_edge("reviewer", END)

# --- 7. Compile ---
app = workflow.compile()
