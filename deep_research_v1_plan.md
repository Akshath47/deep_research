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
