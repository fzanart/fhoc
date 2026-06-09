---
license: mit
title: fhoc
sdk: gradio
emoji: 🐨
colorFrom: blue
colorTo: red
sdk_version: 6.5.1
app_file: main.py
---
# Fighting Harmful Online Communication

## Supporting Climate Journalism in Australia: An AI-based tool to detect and counter climate misinformation

The project "Supporting Climate Journalism in Australia: An AI-based tool to detect and counter climate misinformation" is part of a University of Melbourne Hallmark Research Initiative on "Fighting Harmful Online Communication". This project aims to combat this issue through designing an AI model that identifies and corrects problematic climate content in long written and oral text. The goal is to support journalists sift through their sources, e.g. governmental reports, scientific articles, podcast episodes, and recognize climate-related misinformation, biased frames, or false balance.



```mermaid
flowchart TD
    User([User]) --> UI[Gradio Web UI]
    UI --> |Upload PDF| PDF[PDF File]
    UI --> |Enter URL| URL[Article URL]

    PDF --> ExtractPDF["_markdown_from_pdf()\nGoogle LLM transcription"]
    URL --> ExtractURL["_markdown_from_url()\ntrafilatura + pypandoc"]

    ExtractPDF --> MD[Raw Markdown]
    ExtractURL --> MD

    MD --> Clean["clean_markdown()"]
    Clean --> Chunk["get_base_chunks()\n1,000-char chunks"]
    Chunk --> BtnChoice{Analysis selected}

    subgraph Analyses[" "]
        direction TB

        subgraph Debunk["🔍 Claim Debunking"]
            direction TB
            D1["CARDS API · DiscourseLab\nClassify all chunks in parallel"]
            D1 --> D2{Misinformation\nfound?}
            D2 --> |Yes| D3["FLICC model · HuggingFace\nfzanartu/flicc"]
            D3 --> D4["Openrouter LLM\nRebuttal generation + Debunk summary\nrun in parallel via asyncio"]
            D2 --> |No| D5["Default template"]
            D4 --> D6["render_debunk_html()"]
            D5 --> D6
        end

        subgraph Narrative["📰 Narrative Framing"]
            direction TB
            N1["Pass 1 — 3 concurrent classifiers · Openrouter LLM"]
            N1 --> N1a["HVV: Hero / Villain / Victim"]
            N1 --> N1b["Conflict stance"]
            N1 --> N1c["Cultural Story"]
            N1a & N1b & N1c --> N2["Pass 2 — Narrative Frame\nuses Pass 1 labels as input"]
            N2 --> N3["render_narrative_html()"]
        end
    end

    BtnChoice --> |"Claim Debunking"| Debunk
    BtnChoice --> |"Narrative Framing"| Narrative
    Debunk --> Output[HTML Results]
    Narrative --> Output
```

### Directory Structure

```md
FHOC/
├── README.md                    # Project overview and instructions
├── CHANGELOG.md
├── .gitignore
├── .python-version
├── pyproject.toml               # Project configuration
├── requirements.txt
├── packages.txt
├── uv.lock
├── main.py                      # Gradio app entry point
├── src/                         # Source code
│   ├── __init__.py
│   ├── api/                     # API handlers
│   │   ├── __init__.py
│   │   ├── apis.py
│   │   ├── cards.py             # CARDS classification API
│   │   ├── debunk.py            # Claim debunking pipeline
│   │   ├── debunk_summary.py
│   │   ├── narrative.py         # Narrative framing pipeline
│   │   └── rebuttal.py
│   ├── llm/                     # LLM client wrappers
│   │   ├── __init__.py
│   │   └── llms.py
│   ├── prompts/                 # Prompt templates
│   │   ├── __init__.py
│   │   ├── cards.md
│   │   ├── layer_1.md
│   │   ├── layer_2.md
│   │   ├── layer_3.md
│   │   ├── layer_4.md
│   │   └── md_transcript.md
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── chunking.py          # Text chunking utilities
│       ├── custom.css           # Gradio custom styles
│       └── parser_utils.py      # Text parsing utilities
├── data/
│   ├── raw/                     # Original PDF source files
│   ├── md/                      # Converted markdown versions
│   └── json/                    # Processed JSON outputs
└── notebooks/                   # Jupyter exploration notebooks
```