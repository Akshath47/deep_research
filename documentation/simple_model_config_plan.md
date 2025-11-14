# Simple Model Configuration Plan

## Overview
Create a minimal, straightforward system to assign different LLM models to each agent and node from a single configuration file.

---

## 1. Create Config File: `deep_research/config/models.py`

```python
from langchain_openai import ChatOpenAI

# Simple dictionary mapping component names to their models
MODELS = {
    # Agents
    "clarifier": ChatOpenAI(model="gpt-5-nano", temperature=0),
    "decomposer": ChatOpenAI(model="gpt-5-nano", temperature=0),
    "strategist": ChatOpenAI(model="gpt-5-nano", temperature=0),
    "factchecker": ChatOpenAI(model="gpt-5-mini", temperature=0),
    "synthesizer": ChatOpenAI(model="gpt-5", temperature=0),
    "reviewer": ChatOpenAI(model="gpt-5-mini", temperature=0),
    
    # Nodes
    "scraper_node": ChatOpenAI(model="gpt-5-mini", temperature=0),
    "summarizer_node": ChatOpenAI(model="gpt-5-mini", temperature=0),
}

def get_model(component_name: str):
    """Get model for a component"""
    return MODELS.get(component_name, ChatOpenAI(model="gpt-4o", temperature=0))
```

---

## 2. Update Each Agent

For each agent file in `deep_research/agents/`, replace the model initialization:

**Before:**
```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    tools=tools,
    instructions=PROMPT,
    state_schema=ResearchFlowState,
    builtin_tools=[...]
)
```

**After:**
```python
from deepagents import create_deep_agent
from deep_research.config.models import get_model

agent = create_deep_agent(
    tools=tools,
    instructions=PROMPT,
    state_schema=ResearchFlowState,
    builtin_tools=[...],
    model=get_model("agent_name")  # Add this line
)
```

### Files to update:
- `deep_research/agents/clarifier.py` → `get_model("clarifier")`
- `deep_research/agents/decomposer.py` → `get_model("decomposer")`
- `deep_research/agents/strategist.py` → `get_model("strategist")`
- `deep_research/agents/factchecker.py` → `get_model("factchecker")`
- `deep_research/agents/synthesizer.py` → `get_model("synthesizer")`
- `deep_research/agents/reviewer.py` → `get_model("reviewer")`

---

## 3. Update Nodes

Replace model initialization in node files:

### `deep_research/nodes/scraper_node.py`

**Before:**
```python
from deepagents.model import get_default_model

llm = get_default_model()
```

**After:**
```python
from deep_research.config.models import get_model

llm = get_model("scraper_node")
```

### `deep_research/nodes/summarizer_node.py`

**Before:**
```python
from deepagents.model import get_default_model

def summarizer_node(state: ResearcherState) -> Dict[str, Any]:
    llm = get_default_model()
```

**After:**
```python
from deep_research.config.models import get_model

def summarizer_node(state: ResearcherState) -> Dict[str, Any]:
    llm = get_model("summarizer_node")
```

---

## 4. Model Assignments

| Component | Model | Rationale |
|-----------|-------|-----------|
| Synthesizer | gpt-5 | Most critical - final report |
| Fact-Checker | gpt-5-mini | Critical quality control |
| Reviewer | gpt-5-mini | Critical final check |
| Scraper Node | gpt-5-mini | Critical data collection |
| Summarizer Node | gpt-5-mini | Critical information extraction |
| Clarifier | gpt-5-nano | Routine questions |
| Decomposer | gpt-5-nano | Routine splitting |
| Strategist | gpt-5-nano | Routine planning |

---

## Implementation Steps

1. Create `deep_research/config/` directory
2. Create `deep_research/config/models.py` with MODELS dict
3. Update each agent file (6 files)
4. Update each node file (2 files)
5. Done

---

## To Change Models Later

Just edit the `MODELS` dictionary in `deep_research/config/models.py`:

```python
MODELS = {
    "synthesizer": ChatOpenAI(model="gpt-5-turbo", temperature=0.2),  # Changed
    # ... rest stay the same
}