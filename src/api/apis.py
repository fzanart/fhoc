"""CARDS / Debunk APIs"""

from pathlib import Path
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, computed_field
from ..llm.llms import google_llm, openai_llm

# Construct the path to the cards.md file
current_file_path = Path(__file__).resolve()
prompts_dir = current_file_path.parent.parent / "prompts"
cards_prompt_path = prompts_dir / "cards.md"
cards_prompt = cards_prompt_path.read_text()

# print(google_llm.profile)

CATEGORY_NAMES = {
    "0": "Not climate misinformation",
    "1.1": "Ice/permafrost/snow cover isn't melting",
    "1.2": "We're heading into an ice age/global cooling",
    "1.3": "Weather is cold/snowing",
    "1.4": "Climate hasn't warmed/changed over the last (few) decade(s)",
    "1.6": "Sea level rise is exaggerated/not accelerating",
    "1.7": "Extreme weather isn't increasing/has happened before/isn't linked to climate change",
    "2.1": "It's natural cycles/variation",
    "2.2": "There's no evidence for greenhouse effect/carbon dioxide driving climate change",
    "3.1": "Climate sensitivity is low/negative feedbacks reduce warming",
    "3.2": "Species/plants/reefs aren't showing climate impacts/are benefiting from climate change",
    "3.3": "CO2 is beneficial/not a pollutant",
    "4.1": "Climate policies (mitigation or adaptation) are harmful",
    "4.2": "Climate policies are ineffective/flawed",
    "4.4": "Clean energy technology/biofuels won't work",
    "4.5": "People need energy (e.g. from fossil fuels/nuclear)",
    "5.1": "Climate-related science is unreliable/uncertain/unsound (data, methods & models)",
    "5.2": "Climate movement is unreliable/alarmist/corrupt",
}


class CategoryResponse(BaseModel):
    category: str

    @computed_field
    @property
    def description(self) -> str:
        return CATEGORY_NAMES.get(self.category, "Unknown category")


def classify_text(text: str) -> CategoryResponse:
    prompt = PromptTemplate.from_template(
        cards_prompt + "\n\nUser Query:\n{query}\n\nResponse:"
    )
    llm_with_structure = openai_llm.with_structured_output(CategoryResponse)

    chain = prompt | llm_with_structure
    response = chain.invoke({"query": text})

    return response
