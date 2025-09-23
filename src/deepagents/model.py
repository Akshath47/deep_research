# from langchain_anthropic import ChatAnthropic


# def get_default_model():
#     return ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens=64000)

from langchain_openai import ChatOpenAI

def get_default_model():
    return ChatOpenAI(model="gpt-4o", temperature=0)
