"use langchain to instantiate llms"

import os
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

google_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=128000,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
# openai_llm = ChatOpenAI(model="gpt-5-mini-2025-08-07", temperature=0)

google_search_tool = types.Tool(google_search=types.GoogleSearch())
google_url_context_tool = types.Tool(url_context=types.UrlContext())


google_llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.0,
    max_tokens=128000,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

google_llm_with_search_tool = google_llm.bind_tools(
    tools=[google_search_tool],
)

google_llm_with_url_context = google_llm.bind_tools(
    tools=[google_url_context_tool],
)
