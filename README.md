# Deep Research Agent

This project implements a multi-agent deep research assistant using LangGraph and extending the ideas in the DeepAgents library. It orchestrates a team of specialized agents — Clarifier, Decomposer, Strategist, Researcher, Fact-Checker, Synthesizer, and Reviewer — each operating over a shared virtual filesystem.

## Features

- Human-in-the-loop clarifications with interruptible agents
- Parallel map–reduce research across subqueries
- Structured fact-checking and contradiction detection
- End-to-end report generation with citations and gap analysis
- Configurable model selection per agent
- Virtual filesystem for agent collaboration

## Prerequisites

- Python 3.11 or higher
- pip or uv for package management
- API keys for:
  - OpenAI (for GPT models)
  - Anthropic (optional, for Claude models)
  - Tavily (for web search capabilities)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd deep_research
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- LangGraph and LangGraph CLI
- LangChain core libraries
- LangChain integrations (OpenAI, Anthropic)
- Tavily Python client for web search
- Additional utilities (python-dotenv)

The package will be installed in editable mode (`-e .`) for local development.

### 4. Set Up Environment Variables

Create a `.env` file in the project root with your API keys:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional (if using Anthropic models)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

To obtain API keys:
- **OpenAI**: Sign up at https://platform.openai.com/ and generate an API key
- **Tavily**: Sign up at https://tavily.com/ for web search API access
- **Anthropic**: Sign up at https://console.anthropic.com/ (optional)

### 5. Configure Models (Optional)

The system uses model configurations defined in `deep_research/config/models.py`. By default, it uses:
- GPT-5-mini for most agents (clarifier, decomposer, strategist, fact-checker, reviewer)
- GPT-5 for the synthesizer agent

You can modify the model assignments in `deep_research/config/models.py` to use different models or adjust temperature settings.

## Running the Deep Research Agent

### Using LangGraph CLI

The recommended way to run the agent is using the LangGraph CLI with the in-memory server:

```bash
langgraph dev
```

This will start a local development server where you can interact with the research workflow.

### Programmatic Usage

You can also import and use the compiled graph directly in your Python code:

```python
from deep_research.graphs.workflow import app
from deep_research.state import ResearchFlowState

# Initialize state with your research query
initial_state = {
    "query": "Your research question here",
    "files": {}
}

# Run the workflow
result = app.invoke(initial_state)

# Access the generated research report and other files
print(result["files"])
```

## Project Structure

```
deep_research/
├── agents/              # Specialized agent implementations
│   ├── clarifier.py    # Clarifies ambiguous queries
│   ├── decomposer.py   # Breaks down complex questions
│   ├── strategist.py   # Plans research strategy
│   ├── researcher.py   # Conducts research
│   ├── factchecker.py  # Verifies facts and detects contradictions
│   ├── synthesizer.py  # Synthesizes findings into reports
│   └── reviewer.py     # Reviews and validates final output
├── config/             # Configuration files
│   └── models.py       # Model assignments per agent
├── graphs/             # LangGraph workflow definitions
│   ├── workflow.py     # Main research workflow
│   └── researcher_hub.py  # Parallel research subgraph
├── nodes/              # Custom node implementations
│   ├── scraper_node.py    # Web scraping functionality
│   └── summarizer_node.py # Content summarization
├── tools/              # Agent tools and utilities
│   ├── clarification.py   # Clarification tools
│   └── web_search.py      # Web search integration
├── utils/              # Helper utilities
│   ├── file_system.py  # Virtual filesystem implementation
│   └── prompts.py      # Prompt templates
└── state.py            # Shared state definitions
```

## Workflow Overview

The deep research workflow consists of the following stages:

1. **Clarifier**: Identifies ambiguities and asks clarifying questions
2. **Decomposer**: Breaks down the research question into sub-questions
3. **Strategist**: Plans the research approach for each sub-question
4. **Researcher Hub**: Executes parallel research across sub-questions
5. **Fact-Checker**: Validates findings and identifies contradictions
6. **Synthesizer**: Combines research into a comprehensive report
7. **Reviewer**: Performs final quality checks and gap analysis

## Customization

### Modifying Agent Behavior

Each agent is defined in the `deep_research/agents/` directory. You can customize their behavior by modifying the respective agent files.

### Changing Models

To use different models for specific agents, edit `deep_research/config/models.py`:

```python
MODELS = {
    "clarifier": ChatOpenAI(model="gpt-4", temperature=0),
    "synthesizer": ChatOpenAI(model="gpt-4-turbo", temperature=0.3),
    # ... other agents
}
```

### Adding New Tools

New tools can be added in the `deep_research/tools/` directory and integrated into agent definitions.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure the package is installed in editable mode:

```bash
pip install -e .
```

### API Key Issues

Verify that your `.env` file is in the project root and contains valid API keys. You can test them:

```python
from dotenv import load_dotenv
import os

load_dotenv()
print(os.getenv("OPENAI_API_KEY"))  # Should print your key
```

### Missing Dependencies

If you encounter missing dependencies, reinstall requirements:

```bash
pip install --upgrade -r requirements.txt
```
