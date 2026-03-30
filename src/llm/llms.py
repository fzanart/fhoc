"use langchain to instantiate llms"

import os
from langchain_openrouter import ChatOpenRouter

google_llm = ChatOpenRouter(
    model="google/gemini-2.5-flash",
    temperature=0,
    max_tokens=128000,
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
)

google_llm_pro = ChatOpenRouter(
    model="google/gemini-2.5-pro",
    temperature=0.0,
    max_tokens=128000,
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
)

google_llm_with_search_tool = ChatOpenRouter(
    model="google/gemini-2.5-flash:online",
    temperature=0,
    max_tokens=128000,
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
)
