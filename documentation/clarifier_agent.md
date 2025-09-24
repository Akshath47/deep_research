# Clarifier Agent Documentation

## Overview
The Clarifier Agent is the first step in the research pipeline, transforming vague user queries into clear research briefs through human-in-the-loop interaction.

## Key Components

### Agent Implementation (agents/clarifier.py)
- **Framework**: Built with deepagents framework
- **Tools**: Custom clarification tools + built-in file tools (write_file, read_file, ls, edit_file)
- **Interrupt Config**: Allows humans to accept, edit, or respond to clarifying questions
- **State**: Uses ResearchFlowState for virtual filesystem integration

### Custom Tools (tools/clarification.py)
1. **ask_clarifying_question()**: Presents up to 3 focused questions to users via human interrupt
2. **finalize_clarified_query()**: Creates structured research brief and saves to clarified_query.md

### Prompt (CLARIFIER_AGENT_PROMPT)
- Guides the LLM through clarification workflow
- Includes few-shot examples for different query types
- Ensures structured output format

## Workflow
1. Analyze user's initial query
2. Ask 2-3 clarifying questions using ask_clarifying_question tool
3. Wait for human responses via interrupt mechanism
4. Iterate if needed (max 2-3 rounds)
5. Finalize clarified query with finalize_clarified_query tool
6. Save to clarified_query.md

## Output Format (clarified_query.md)
```
# Clarified Research Query

## Original Query
[user's initial query]

## Clarifications Received
[summary of user responses]

## Refined Research Objective
[clear objective statement]

## Research Scope and Boundaries
[specific scope definition]

## Key Questions to Answer
[numbered list of questions]

## Expected Deliverable Format
[output format specification]
```

## Why Human-in-the-Loop?
- **Accuracy**: Direct user input prevents misinterpretation of vague queries
- **Flexibility**: Handles novel or complex requirements that AI alone might miss
- **Trust**: Users can correct misunderstandings early in the process
- **Quality Control**: Ensures research stays focused on actual user needs

## Integration
- **Inputs**: User's initial research query
- **Outputs**: clarified_query.md (passed to decomposer agent)
- **File System**: Uses virtual filesystem for data persistence
- **State Management**: Maintains context across interactions

## Advantages Over Automated Systems
1. **Handles Ambiguity**: Can clarify vague or complex queries
2. **Contextual Understanding**: Considers domain-specific nuances
3. **User Control**: Allows humans to guide the research direction
4. **Audit Trail**: Documents the clarification process for transparency