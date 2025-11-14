This project implements a multi-agent deep research assistant using LangGraph and extending the ideas in the DeepAgents library.
It orchestrates a team of specialized agents — Clarifier, Decomposer, Strategist, Researcher, Fact-Checker, Synthesizer, and Reviewer — each operating over a shared virtual filesystem.
The system supports:

Human-in-the-loop clarifications with interruptible agents

Parallel map–reduce research across subqueries

Structured fact-checking and contradiction detection

End-to-end report generation with citations and gap analysis

