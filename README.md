# Fighting Harmful Online Communication

## Supporting Climate Journalism in Australia: An AI-based tool to detect and counter climate misinformation

The project "Supporting Climate Journalism in Australia: An AI-based tool to detect and counter climate misinformation" is part of a University of Melbourne Hallmark Research Initiative on "Fighting Harmful Online Communication". This project aims to combat this issue through designing an AI model that identifies and corrects problematic climate content in long written and oral text. The goal is to support journalists sift through their sources, e.g. governmental reports, scientific articles, podcast episodes, and recognize climate-related misinformation, biased frames, or false balance.


### Directory Structure

```md
FHOC/
├── README.md                # Project overview and instructions
├── .gitignore               # Files and directories to be ignored by Git
├── .python-version 
├── pyproject.toml           # Project configuration
├── main.py
├── src/                     # Source code
│   ├── __init__.py          # Initializes the src package
│   ├── llm/
│   │   ├── __init__.py
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── chunking.py      # Text chunking utilities
│   │   ├── parser.py        # Text parsing utilities
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── cards.md       # Prompts for the CARDS model
```
