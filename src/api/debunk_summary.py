from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from ..llm.llms import google_llm


class DebunkSummaryResult(BaseModel):
    article_summary: str = Field(
        description="Concise summary of what the article is about"
    )
    debunking_summary: str = Field(
        description="Concise analysis of the main denial tactics used in the article"
    )


PROMPT_DEBUNK_SUMMARY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """... FILL IN YOUR INSTRUCTION HERE ...
                                                                                                                                                        
Article:
{text}                                                                                                                                                 
                                                                                                                                                        
FLICC denial techniques detected: {flicc_labels}
CARDS misinformation categories detected:                                                                                                              
{cards_categories}                                                                                                                                     
""",
        )
    ]
)

chain_debunk_summary = PROMPT_DEBUNK_SUMMARY | google_llm.with_structured_output(
    DebunkSummaryResult
)


async def generate_debunk_summary(
    text: str,
    flicc_labels: list[str],
    cards_categories: list[str],
) -> DebunkSummaryResult:
    return await chain_debunk_summary.ainvoke(
        {
            "text": text,
            "flicc_labels": ", ".join(flicc_labels) if flicc_labels else "none",
            "cards_categories": (
                "\n".join(cards_categories) if cards_categories else "none"
            ),
        }
    )
