"""
narrative.py — Narrative Media Framing analysis for fhoc.

Implements the framework from:
  Otmakhova & Frermann (2025), "Narrative Media Framing in Political Discourse"
  ACL 2025 Findings. https://aclanthology.org/2025.findings-acl.477

Classification pipeline (two-pass structured approach):
  Pass 1 — Three concurrent classifiers:
    - Table 6: Hero / Villain / Victim stakeholders + Focus
    - Table 7: Conflict / Resolution stance
    - Table 8: Cultural Story
  Pass 2 (Table 10) — Narrative Frame using Pass 1 labels as structured input.

Usage:
    from narrative import analyze_components
    result = await analyze_components(text)
"""

import asyncio
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from ..llm.llms import google_llm

# ---------------------------------------------------------------------------
# Classes and labels
# ---------------------------------------------------------------------------

HVV_CLASSES = {
    "GOVERNMENTS_POLITICIANS": "governments and political organizations",
    "INDUSTRY_EMISSIONS": "industries, businesses, and the pollution created by them",
    "LEGISLATION_POLICIES": "policies and legislation responses",
    "GENERAL_PUBLIC": "general public, individuals, and society, including their wellbeing, status quo and economy",
    "ANIMALS_NATURE_ENVIRONMENT": "nature and environment in general or specific species",
    "ENV.ORGS_ACTIVISTS": "climate activists and organizations",
    "SCIENCE_EXPERTS_SCI.REPORTS": "scientists and scientific reports/research",
    "CLIMATE_CHANGE": "climate change as a process or consequence",
    "GREEN_TECHNOLOGY_INNOVATION": "innovative and green technologies",
    "MEDIA_JOURNALISTS": "media and journalists",
}

STORY_CLASSES = {
    "HIERARCHICAL": "this story assumes that the situation can be controlled externally, but we need to be bound by tight social prescriptions and group actions.",
    "INDIVIDUALISTIC": "this story assumes that the situation cannot be controlled externally, and no group actions are necessary.",
    "EGALITARIAN": "this story assumes that the situation requires combined efforts and group actions of all members of society.",
}

CONFLICT_CLASSES = {
    "FUEL_RESOLUTION": "the article proposes or describes specific measures, policies, or events that would contribute to the resolution of the climate crisis.",
    "FUEL_CONFLICT": "the article proposes or describes specific measures, policies, or events that would exacerbate the climate crisis.",
    "PREVENT_RESOLUTION": "the article criticises measures, policies, or events that contribute to the resolution of the climate crisis; or it denies the climate crisis.",
    "PREVENT_CONFLICT": "the article criticises measures, policies, or events that exacerbate the climate crisis; or it provides the evidence for the climate crisis.",
}

NARRATIVES_CLASSES = {
    "12_YEARS": """12 Years to save the world - Past and present human action (or inaction) risks a catastrophic future climatic event unless people change their behaviour to mitigate climate change. The villain here is government or industry pollution, and the victim is environment, people, or climate change. The narratives focuses on villain and shows how they deny climate change or abandon climate policies.""",
    "ALL_GOING_TO_DIE": """We are all going to die - This narrative shows the current or potential catastrophic impact of climate change on people. The villain here is climate change or industry emissions, and the victim is general public. The narrative focuses on victim and raises the alarm.""",
    "ALL_TALK": """All talk little action - This narrative emphasises inconcistency between ambitious climate action targets and actual actions. The villain here is government and politicians, and the victim is often climate change. The narrative focuses on villain who reneged on their promise to support climate policies.""",
    "CARBON_EXPANSION": """Carbon-fuelled expansion - The free market is at the centre of this narrative which presents action on climate change as an obstacle to the freedom and well-being of citizens. The villain here is climate policies or green technologies, and the victim is general public or old industries. The narrative focuses on victim and advocates for abandoning climate policies.""",
    "CLIMATE_SOLUTIONS_WONT_WORK": """Climate solutions won't work. Climate policies are harmful and a threat to society and the economy. Climate policies are ineffective and too difficult to implement. The villain is here climate policies or green technologies, and the victim is usually general public. The narrative focuses on villain and criticizes them.""",
    "COLLAPSE_IS_IMMINENT": """The climate crisis is due to the inaction of the negligent or complacent politicians, and it is incumbent upon individuals to shock society into urgent action. The heroes here are environmental activists, and the villain is government. The narrative focuses on villain and advocated for taking action such as protests or disobedience.""",
    "DEBATE_AND_SCAM": """The heroes of this narrative are sceptical individuals who dare to challenge the false consensus on climate change which is propagated by those with vested interests. The villains are governments, activists, journalist and policies that support climate measures. The narrative focuses on villains and exposes them.""",
    "ENDANGERED_SPECIES": """Endangered species (like polar bears) are the helpless victims of this narrative, who are seeing their habitat destroyed by the actions of villainous humans. The villain here can be government, legislation, industry, and the victim is environment and nature. The narrative focuses on victims and shows how they are endangered.""",
    "EVERY_LITTLE_HELPS": """This narrative presents a society which has transitioned to a sustainable 'green' way of life. Could be by portraying individuals as the protagonists of stories that propose solutions to climate change. The heroes here are individuals and common people, and it is implied that they are also a villain. The narrative focuses on hero and shows how they change their consumption.""",
    "GORE": """This is a narrative of scientific discovery which climaxes on the certainty that climate change is unequivocally caused by humans. The heroes here are scientists, the villain is government, general public, or industry pollution, and the victim is environment or climate change. The narrative focuses on villain and raises alarm.""",
}

FocusLabel = Literal["HERO", "VILLAIN", "VICTIM"]
StakeholderLabel = Literal[*HVV_CLASSES.keys()]
StoryLabel = Literal[*STORY_CLASSES.keys()]
ConflictLabel = Literal[*CONFLICT_CLASSES.keys()]
NarrativeLabel = Literal[*NARRATIVES_CLASSES.keys()]

# ---------------------------------------------------------------------------
# Pydantic schemas for structured output
# ---------------------------------------------------------------------------


class HVVResult(BaseModel):
    """Table 6 — Hero, Villain, Victim stakeholders and narrative focus."""

    hero_class: StakeholderLabel = Field(
        description="Stakeholder category of the hero, or 'None'"
    )
    villain_class: StakeholderLabel = Field(
        description="Stakeholder category of the villain, or 'None'"
    )
    victim_class: StakeholderLabel = Field(
        description="Stakeholder category of the victim, or 'None'"
    )
    focus: FocusLabel = Field(description="Which character the article focuses on")


class StoryResult(BaseModel):
    """Table 7 — Cultural story."""

    story: StoryLabel = Field(description="The cultural story reflected in the article")


class ConflictResult(BaseModel):
    """Table 8 — Conflict/resolution stance."""

    conflict: ConflictLabel = Field(
        description="How the article relates to the climate crisis"
    )


class NarrativeResult(BaseModel):
    """Table 10 — Specific narratives."""

    narrative: NarrativeLabel = Field(
        description="The specific narrative reflected in the article"
    )
    explanation: str = Field(
        description=(
            "Brief explanation of how the identified hero, villain, victim, focus, "
            "conflict type, and cultural story combine to produce this specific narrative frame."
        )
    )


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------


PROMPT_HVV = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a social scientist specializing in climate change. You will be given a newspaper article and asked who is framed as a hero, villain or a victim in it.
For each of these categories, you will be also asked to specify the corresponding word or phrase, and to classify it into the following classes:

{classes}

Finally, you need to detect which of the characters (hero, villain, or victim) the news story is focusing on.

Article:

{text}""",
        )
    ]
)

PROMPT_STORY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a social scientist specializing in climate change.
You will be given a newspaper article and asked what is the cultural story reflected in it.
You should choose one of the following classes:

{classes}

Article:
{text}""",
        )
    ]
)

PROMPT_CONFLICT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a social scientist specializing in climate change.
You will be given a newspaper article and asked to identify how it relates to climate crisis.
Assign one of the following classes:

{classes}

Article:
{text}""",
        )
    ]
)

PROMPT_NARRATIVE = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a social scientist specializing in climate change. 
You will be given a newspaper article and asked what is the main narrative in it. You should choose one of the following classes:

{classes}   

Article:
{text}
            
            
The article has the following narrative framing components according to the framework described in the research paper "Narrative Media Framing in Political Discourse":

1. Hero (entities portrayed positively): {hero_class}
2. Villain (entities portrayed negatively): {villain_class}
3. Victim (entities portrayed as suffering): {victim_class}
4. Focus (whether the narrative focuses on hero, villain, or victim): {focus}
5. Conflict type (fuel conflict, fuel resolution, prevent conflict, prevent resolution): {conflict_type}
6. Cultural story (individualistic, hierarchical, egalitarian, fatalistic): {cultural_story}

""",
        )
    ]
)

# ---------------------------------------------------------------------------
# Chains — prompt | llm.with_structured_output(schema)
# ---------------------------------------------------------------------------

chain_hvv = PROMPT_HVV | google_llm.with_structured_output(HVVResult)
chain_story = PROMPT_STORY | google_llm.with_structured_output(StoryResult)
chain_conflict = PROMPT_CONFLICT | google_llm.with_structured_output(ConflictResult)
chain_narrative = PROMPT_NARRATIVE | google_llm.with_structured_output(NarrativeResult)

# ---------------------------------------------------------------------------
# Async classifiers
# ---------------------------------------------------------------------------


def _format_classes(classes: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in classes.items())


async def _classify_hvv(text: str) -> HVVResult:
    return await chain_hvv.ainvoke(
        {
            "classes": _format_classes(HVV_CLASSES),
            "text": text,
        }
    )


async def _classify_story(text: str) -> StoryResult:
    return await chain_story.ainvoke(
        {
            "classes": _format_classes(STORY_CLASSES),
            "text": text,
        }
    )


async def _classify_conflict(text: str) -> ConflictResult:
    return await chain_conflict.ainvoke(
        {
            "classes": _format_classes(CONFLICT_CLASSES),
            "text": text,
        }
    )


# ---------------------------------------------------------------------------
# Pass 1 — run all three classifiers concurrently
# ---------------------------------------------------------------------------


async def _pass1(text: str) -> tuple[HVVResult, StoryResult, ConflictResult]:
    hvv, story, conflict = await asyncio.gather(
        _classify_hvv(text),
        _classify_story(text),
        _classify_conflict(text),
    )
    return hvv, story, conflict


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def analyze_components(text: str) -> dict:
    """Run the full two-pass narrative framing analysis on a plain-text article.

    Returns a dict with keys: hvv, story, conflict, narrative.
    """
    hvv, story, conflict = await _pass1(text)

    narrative = await chain_narrative.ainvoke(
        {
            "classes": _format_classes(NARRATIVES_CLASSES),
            "text": text,
            "hero_class": (HVV_CLASSES.get(hvv.hero_class)).title(),
            "villain_class": (HVV_CLASSES.get(hvv.villain_class)).title(),
            "victim_class": (HVV_CLASSES.get(hvv.victim_class)).title(),
            "focus": (hvv.focus).title(),
            "conflict_type": (conflict.conflict).title(),
            "cultural_story": (story.story).replace("_", " "),
        }
    )

    return {
        "hvv": hvv,
        "story": story,
        "conflict": conflict,
        "narrative": narrative,
    }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def render_narrative_html(result: dict) -> str:
    """
    Takes the dict returned by analyze_components() and returns
    a self-contained HTML string ready for gr.HTML().

    Args:
        result: dict with keys hvv, story, conflict, narrative
                (as returned by analyze_components)
    Returns:
        HTML string
    """
    hvv: HVVResult = result["hvv"]
    story: StoryResult = result["story"]
    conflict: ConflictResult = result["conflict"]
    narrative: NarrativeResult = result["narrative"]

    hero = HVV_CLASSES.get(hvv.hero_class, hvv.hero_class)
    villain = HVV_CLASSES.get(hvv.villain_class, hvv.villain_class)
    victim = HVV_CLASSES.get(hvv.victim_class, hvv.victim_class)
    focus = HVV_CLASSES.get(hvv.focus, hvv.focus)
    conflict_label = CONFLICT_CLASSES.get(conflict.conflict, conflict.conflict)
    story_label = STORY_CLASSES.get(story.story, story.story)
    narrative_label = NARRATIVE_CLASSES.get(narrative.narrative, narrative.narrative)

    cards = [
        ("🦸", "Hero", hero),
        ("🦹", "Villain", villain),
        ("😢", "Victim", victim),
        ("🎯", "Focus", focus),
        ("⚔️", "Conflict", conflict_label),
        ("🏛️", "Cultural Story", story_label),
    ]

    cards_html = "\n".join(
        f"""
        <div class="nf-card">
            <div class="nf-card-icon">{icon}</div>
            <div class="nf-card-label">{label}</div>
            <div class="nf-card-value">{value}</div>
        </div>"""
        for icon, label, value in cards
    )

    return f"""
<style>
  .nf-wrapper {{
      font-family: inherit;
      padding: 4px;
  }}
  .nf-section-title {{
      font-size: 1rem;
      font-weight: 600;
      color: #374151;
      margin: 0 0 12px 0;
      padding-bottom: 6px;
      border-bottom: 2px solid #e5e7eb;
  }}
  .nf-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 16px;
  }}
  .nf-card {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 12px 10px;
      text-align: center;
  }}
  .nf-card-icon {{
      font-size: 1.4rem;
      margin-bottom: 4px;
  }}
  .nf-card-label {{
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #6b7280;
      margin-bottom: 4px;
  }}
  .nf-card-value {{
      font-size: 0.85rem;
      font-weight: 600;
      color: #1f2937;
  }}
  .nf-narrative-block {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 12px;
  }}
  .nf-narrative-label {{
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #3b82f6;
      margin-bottom: 4px;
  }}
  .nf-narrative-value {{
      font-size: 1rem;
      font-weight: 700;
      color: #1e40af;
  }}
  .nf-explanation {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 14px;
  }}
  .nf-explanation-title {{
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #6b7280;
      margin-bottom: 6px;
  }}
  .nf-explanation-text {{
      font-size: 0.85rem;
      color: #374151;
      line-height: 1.6;
      margin: 0;
  }}
</style>

<div class="nf-wrapper">
  <p class="nf-section-title">📰 Narrative Framing Analysis</p>

  <div class="nf-grid">
    {cards_html}
  </div>

  <div class="nf-narrative-block">
    <div class="nf-narrative-label">Narrative Frame</div>
    <div class="nf-narrative-value">{narrative_label}</div>
  </div>

  <div class="nf-explanation">
    <div class="nf-explanation-title">Detailed Analysis</div>
    <p class="nf-explanation-text">{narrative.explanation}</p>
  </div>
</div>
"""
