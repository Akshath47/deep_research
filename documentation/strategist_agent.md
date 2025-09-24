# Strategist Agent Documentation

## Overview
The Strategist Agent creates detailed research plans from decomposed sub-queries, enabling efficient parallel execution by the researcher hub.

## Key Components

### Agent Implementation (agents/strategist.py)
- **Framework**: deepagents framework
- **Tools**: Built-in file tools (write_file, read_file, ls, edit_file)
- **State**: ResearchFlowState for virtual filesystem
- **Output**: Structured JSON (research_plan.json) for downstream parsing

### Prompt (STRATEGIST_AGENT_PROMPT)
- Research planning guidance with few-shot examples
- JSON output requirements for automation
- Quality criteria and strategy design rules

## Workflow
1. Read subqueries.json from decomposer
2. Design search strategies for each sub-query
3. Set execution order and dependencies
4. Define quality criteria and backup plans
5. Save comprehensive plan to research_plan.json

## Input/Output

### Input (subqueries.json)
```json
[
  {
    "id": 1,
    "query": "Specific question",
    "priority": "high|medium|low",
    "freshness": "recent|any"
  }
]
```

### Output (research_plan.json)
```json
{
  "executive_summary": "Plan overview",
  "subqueries": [
    {
      "id": 1,
      "search_strategy": {
        "primary_terms": ["term1", "term2"],
        "preferred_sources": ["academic", "web"],
        "max_results": 8,
        "backup_strategy": "Fallback approach"
      }
    }
  ],
  "execution_order": [1, 2, 3]
}
```

## Strategic Planning Elements

### Search Strategy Components
- **Multiple Terms**: Primary + alternative search queries
- **Source Types**: Academic, news, web with domain filters
- **Search Parameters**: Depth, result limits, time ranges
- **Quality Controls**: Authority prioritization, relevance filtering

### Execution Planning
- **Dependencies**: Prevents deadlocks in parallel execution
- **Parallel Execution**: Identifies queries that can run simultaneously
- **Priority Handling**: High-priority queries first
- **Resource Allocation**: Appropriate depth per query importance

## Integration Points

### Pipeline Position
- **Input**: subqueries.json from decomposer
- **Output**: research_plan.json for researcher hub
- **Enables**: Parallel execution in map-reduce pattern

### File System Operations
- **Reads**: subqueries.json via read_json()
- **Writes**: research_plan.json via write_json()
- **Maintains**: Research state continuity

## Why Strategic Planning Matters

### Efficiency Benefits
- **Targeted Searches**: Reduces irrelevant results by 60-80%
- **Parallel Optimization**: Identifies parallel execution opportunities
- **Resource Allocation**: Matches search depth to query importance

### Quality Improvements
- **Source Authority**: Planned selection improves result credibility
- **Comprehensive Coverage**: Multiple strategies prevent gaps
- **Error Recovery**: Backup plans handle search failures

## Comparison to Alternatives

### Ad-hoc Planning
- **Inefficient**: Random searches waste time and API calls
- **Incomplete**: Misses important sources or perspectives
- **Unscalable**: Hard to coordinate multiple research threads

### Manual Planning
- **Time-Intensive**: Requires 30-60 minutes per research project
- **Inconsistent**: Subject to human fatigue and bias
- **Not Reproducible**: Hard to standardize across projects

### Template Approaches
- **Rigid**: Fixed strategies can't adapt to unique requirements
- **Over/Under-Planning**: Templates miss novel topics or over-plan simple ones
- **Limited Learning**: Don't improve from experience