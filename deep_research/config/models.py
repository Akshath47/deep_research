from langchain_openai import ChatOpenAI

# Model configurations to avoid typos when changing values
GPT_5_NANO = ChatOpenAI(model="gpt-5-nano", temperature=0)
GPT_5_MINI = ChatOpenAI(model="gpt-5-mini", temperature=0)
GPT_5 = ChatOpenAI(model="gpt-5", temperature=0)

# Simple dictionary mapping component names to their models
MODELS = {
    # Agents
    "clarifier": GPT_5_MINI,
    "decomposer": GPT_5_MINI,
    "strategist": GPT_5_MINI,
    "factchecker": GPT_5_MINI,
    "synthesizer": GPT_5,
    "reviewer": GPT_5_MINI,

    # Nodes
    "scraper_node": GPT_5_MINI,
    "summarizer_node": GPT_5_MINI,
}

def get_model(component_name: str):
    """Get model for a component"""
    return MODELS.get(component_name, GPT_5_MINI)