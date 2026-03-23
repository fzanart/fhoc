import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List


client = OpenAI(
    api_key=os.getenv("CARDS"),
    base_url="https://api.discourselab.ai/v1",
)


class Category(BaseModel):
    category: str
    description: str


class Categories(BaseModel):
    categories: List[Category]


def classify_text(text: str):
    response = client.beta.chat.completions.parse(
        model="cards-mini-sonnet-2024-12-05",
        messages=[{"role": "user", "content": text}],
        response_format=Categories,
        extra_body={"prompt_id": "cards"},
        temperature=0,
    )

    result = response.choices[0].message.parsed
    return result.categories[0]
