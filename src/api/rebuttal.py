import random
from pathlib import Path
from collections import namedtuple
from langchain_core.prompts import PromptTemplate
#from transformers import pipeline
from ..llm.llms import google_llm_with_search_tool, google_llm

PROMPT_DIR = Path(__file__).parent.parent / "prompts"

fact_prompt_text = (PROMPT_DIR / "layer_1.md").read_text()
summary_prompt_text = (PROMPT_DIR / "layer_2.md").read_text()
fallacy_prompt_text = (PROMPT_DIR / "layer_3.md").read_text()
closing_fact_prompt_text = (PROMPT_DIR / "layer_4.md").read_text()

DEFINITIONS = {
    "ad hominem": "Attacking a person/group instead of addressing their arguments.",
    "anecdote": "Using personal experience or isolated examples instead of sound arguments or compelling evidence.",
    "cherry picking": "Selecting data that appear to confirm one position while ignoring other data that contradicts that position.",
    "conspiracy theory": "Proposing that a secret plan exists to implement a nefarious scheme such as hiding a truth.",
    "fake experts": "Presenting an unqualified person or institution as a source of credible information.",
    "false choice": "Presenting two options as the only possibilities, when other possibilities exist.",
    "false equivalence": "Incorrectly claiming that two things are equivalent, despite the fact that there are notable differences between them.",
    "impossible expectations": "Demanding unrealistic standards of certainty before acting on the science.",
    "misrepresentation": "Misrepresenting a situation or an opponent's position in such a way as to distort understanding.",
    "oversimplification": "Simplifying a situation in such a way as to distort understanding, leading to erroneous conclusions.",
    "single cause": "Assuming a single cause or reason when there might be multiple causes or reasons.",
    "slothful induction": "Ignoring relevant evidence when coming to a conclusion",
}

#pipe = pipeline("text-classification", model="fzanartu/flicc")
llm = google_llm
llm_with_search_tool = google_llm_with_search_tool


class RebuttalStructure:
    def __init__(self):
        # hamburger-style structure:
        self.heading = namedtuple("Heading", ["name", "content"])
        self.rebuttal = [
            self.heading(name="Myth", content=None),
            self.heading(name="##FACT", content=None),
            self.heading(name="##MYTH", content=None),
            self.heading(name="##FALLACY", content=None),
            self.heading(name="##FACT", content=None),
        ]

    def generate_chain(self, prompt_text, llm):
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm

        return chain

    def run(self, misinformation):
        # --- Build chains ---
        fact_chain = self.generate_chain(
            prompt_text=fact_prompt_text,
            llm=llm_with_search_tool,
        )

        print(fact_chain)

        summary_chain = self.generate_chain(
            prompt_text=summary_prompt_text,
            llm=llm,
        )

        fallacy_chain = self.generate_chain(
            prompt_text=fallacy_prompt_text,
            llm=llm,
        )

        closing_fact_chain = self.generate_chain(
            prompt_text=closing_fact_prompt_text,
            llm=llm,
        )

        # --- Generate content ---
        opening_fact = fact_chain.invoke({"misinformation": misinformation})

        print(opening_fact)

        summary = summary_chain.invoke({"misinformation": misinformation})

        # pick a random fallacy, definition form DEFINITIONS
        fallacy = random.choice(DEFINITIONS)
        fallacy_definition = DEFINITIONS[fallacy]

        fallacy_explanation = fallacy_chain.invoke(
            {
                "misinformation": misinformation,
                "fallacy": fallacy,
                "fallacy_definition": fallacy_definition,
                "fact": opening_fact,
            }
        )
        closing_fact = closing_fact_chain.invoke({"fact": opening_fact})

        # --- Populate rebuttal layers ---
        self.rebuttal[1] = self.rebuttal[1]._replace(content=opening_fact.content)
        self.rebuttal[2] = self.rebuttal[2]._replace(content=summary.content)
        self.rebuttal[3] = self.rebuttal[3]._replace(
            content=fallacy_explanation.content
        )
        self.rebuttal[4] = self.rebuttal[4]._replace(content=closing_fact.content)

        # --- Render final output ---
        return "\n".join(
            f"{layer.name}: {layer.content}" for layer in self.rebuttal[1:]
        )
