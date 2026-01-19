"use langchain to instantiate llms"

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

google_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0, max_tokens=128000
)
openai_llm = ChatOpenAI(model="gpt-5-mini-2025-08-07", temperature=0, max_tokens=128000)
