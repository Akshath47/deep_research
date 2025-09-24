# Decomposer Agent Documentation

## Overview
The Decomposer Agent is the second step in the research pipeline, breaking down clarified research queries into smaller, focused sub-queries for parallel execution.

## Key Components

### Agent Implementation (agents/decomposer.py)
- **Framework**: Built with deepagents framework
- **Tools**: Built-in file system tools (write_file, read_file, ls, edit_file)
- **State**: Uses ResearchFlowState for virtual filesystem integration
- **No Custom Tools**: Relies entirely on file operations and LLM reasoning

### Prompt (DECOMPOSER_AGENT_PROMPT)
- Guides the LLM through decomposition workflow
- Includes few-shot examples for different research domains
- Ensures 3-7 focused sub-queries are generated
- Requires structured JSON output format

## Workflow
1. Read clarified_query.md using read_file tool
2. Analyze the research objective, scope, and key questions
3. Break down into independent sub-queries (3-7 typically)
4. Add metadata (priority, freshness, description) to each sub-query
5. Save structured sub-queries to subqueries.json using write_file tool

## Input/Output

### Input (clarified_query.md)
Structured research brief from clarifier agent containing:
- Refined research objective
- Scope and boundaries
- Key questions to answer
- Constraints and requirements

### Output (subqueries.json)
JSON array with sub-query objects:
```json
[
  {
    "id": 1,
    "query": "Specific research question",
    "priority": "high|medium|low",
    "freshness": "recent|any",
    "description": "Brief explanation of what this sub-query covers"
  }
]
```

## Decomposition Strategy

### Principles
- **Independence**: Each sub-query should be independently researchable
- **Coverage**: Collectively cover the entire research scope
- **Focus**: Sub-queries should be specific enough for targeted research
- **Balance**: Aim for 3-7 sub-queries to enable parallel execution without fragmentation

### Metadata Assignment
- **Priority**: Based on importance to main research objective
- **Freshness**: Recent for rapidly changing topics, any for stable information
- **Description**: Clear explanation of sub-query scope and purpose

## Integration with File System

### Virtual Filesystem Operations
- **read_text()**: Reads clarified_query.md content
- **write_json()**: Saves structured sub-queries to subqueries.json
- **State Management**: Updates ResearchFlowState with new files

### Coordination
- **Input Dependency**: Requires clarified_query.md from clarifier agent
- **Output Handover**: Produces subqueries.json for strategist agent
- **Error Handling**: Validates input file existence and content

## Advantages of Decomposition

### Parallel Execution Enablement
- **Speed**: Multiple sub-queries can be researched simultaneously
- **Resource Utilization**: Makes full use of available processing capacity
- **Fault Isolation**: Issues in one sub-query don't affect others

### Research Quality
- **Focused Research**: Each sub-query can be researched with specific strategies
- **Comprehensive Coverage**: Ensures all aspects of the research question are addressed
- **Modular Results**: Easier to combine and synthesize results

## Comparison to Alternatives

### Single Query Approach
- **Limitations**: Can't leverage parallel processing
- **Risk**: Missing important sub-topics
- **Inflexibility**: Hard to adjust research focus mid-process

### Manual Decomposition
- **Inefficiency**: Requires human time and expertise
- **Inconsistency**: Subject to human bias and oversight
- **Scalability**: Doesn't work for complex or unfamiliar topics

### Over-Decomposition
- **Fragmentation**: Too many tiny queries reduce efficiency
- **Coordination Overhead**: Harder to synthesize results
- **Resource Waste**: Underutilizes parallel execution benefits

## Integration Points
- **Predecessor**: Clarifier Agent (clarified_query.md)
- **Successor**: Strategist Agent (subqueries.json)
- **Parallel Path**: Will eventually feed into Researcher Hub for parallel execution
- **State Continuity**: Maintains virtual filesystem state throughout the process