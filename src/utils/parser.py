import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

RAW_DIR = Path("data/raw")
MD_DIR = Path("data/md")
MD_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """Provide a verbatim transcription of this document into Markdown.
- Preserve all content exactly (no summarizing or rewriting)
- Keep the original structure using Markdown headers
- Preserve lists, emphasis, links, tables, code blocks
- Output Markdown only
"""


class MarkdownConverter:
    def __init__(self, model="gemini-2.5-pro"):
        self.model = model

    def run(self):
        for i, pdf in enumerate(RAW_DIR.glob("*.pdf")):
            out = MD_DIR / f"{pdf.stem}.md"
            if out.exists():
                continue

            uploaded = client.files.upload(file=pdf)

            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=[SYSTEM_PROMPT, uploaded],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        max_output_tokens=65536,
                    ),
                )

                out.write_text(response.text, encoding="utf-8")
                print(f"{i}. {pdf.stem} converted")

            finally:
                client.files.delete(name=uploaded.name)


if __name__ == "__main__":
    MarkdownConverter().run()
