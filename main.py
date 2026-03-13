"""
Gradio interface for fighting harmful online communication (fhoc).
"""

import asyncio
import logging
import copy
from pathlib import Path
import gradio as gr
import markdown
import trafilatura
from bs4 import BeautifulSoup
import pypandoc
from langchain_core.messages import HumanMessage
from transformers import pipeline
from src.llm.llms import google_llm
from src.utils.parser_utils import clean_markdown, encode_pdf_to_base64
from src.utils.chunking import get_base_chunks
from src.api.apis import classify_text
from src.api.rebuttal import RebuttalStructure


transcription_prompt = Path("./src/prompts/md_transcript.md").read_text(
    encoding="utf-8"
)

custom_css = Path("./src/utils/custom.css").read_text(encoding="utf-8")

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

pipe = pipeline("text-classification", model="fzanartu/flicc")


async def analyze_chunks(prev_state, progress=gr.Progress()):

    logger.info("Starting chunk analysis")

    chunks = copy.deepcopy(prev_state["chunks"])
    by_id = {c["id"]: c for c in chunks}

    async def classify(chunk):
        resp = await asyncio.to_thread(classify_text, chunk["text"])
        return chunk["id"], resp

    progress(0.2, desc="Classifying text...")
    results = await asyncio.gather(*[classify(c) for c in chunks])

    rebuttal_gen = RebuttalStructure()
    misinfo_chunks = []
    zeros = ("0", "0.0", 0, 0.0)

    for chunk_id, resp in results:

        logger.info(f"Chunk {chunk_id} classified: {resp.category}")

        chunk = by_id[chunk_id]
        chunk["CARDS_code"] = resp.category
        chunk["CARDS_category"] = resp.description
        if resp.category not in zeros:
            chunk["has_misinformation"] = True
            misinfo_chunks.append(chunk_id)

    if misinfo_chunks:

        texts = [by_id[i]["text"] for i in misinfo_chunks]

        logger.info(f"Detecting fallacies for {len(texts)} chunks")

        labels = pipe(texts)

        for chunk_id, result in zip(misinfo_chunks, labels):
            by_id[chunk_id]["fallacy"] = result["label"]

        logger.info(f"Generating rebuttals for {len(misinfo_chunks)} chunks")
        progress(0.5, desc="Generating rebuttals...")

        rebuttal_jobs = [
            (
                chunk_id,
                rebuttal_gen.run(by_id[chunk_id]["text"], by_id[chunk_id]["fallacy"]),
            )
            for chunk_id in misinfo_chunks
        ]

        rebuttal_results = await asyncio.gather(*[job for _, job in rebuttal_jobs])

        for (chunk_id, _), rebuttal in zip(rebuttal_jobs, rebuttal_results):
            by_id[chunk_id]["rebuttal"] = rebuttal

    return {"chunks": list(by_id.values())}


def render_document(state):
    # Your state['chunks'] logic is correct
    html_output = '<div class="text-container">'
    for chunk in state["chunks"]:
        # Convert markdown text to HTML
        text_html = markdown.markdown(chunk.get("text", ""))
        is_bad = chunk.get("has_misinformation", False)
        rebuttal = (
            markdown.markdown(chunk.get("rebuttal"))
            if isinstance(chunk.get("rebuttal"), str)
            else ""
        )

        if is_bad:
            html_output += f"""
            <div class="misinfo-trigger" tabindex="0">
                {text_html}
                <div class="rebuttal-content">
                    <span class="rebuttal-label">⚠️ Rebuttal:</span>
                    {rebuttal}
                </div>
            </div>"""
        else:
            html_output += f'<div class="neutral-chunk">{text_html}</div>'

    html_output += "</div>"
    return html_output


def create_document_state(raw_markdown):
    """Common logic to clean markdown and create the doc_state dictionary."""
    cleaned = clean_markdown(raw_markdown)

    logger.info(f"Markdown cleaned. Length: {len(cleaned)} characters")

    chunks = [
        {
            "id": i,
            "text": c.page_content,
            "start": c.metadata["start_index"],
            "end": c.metadata["start_index"] + len(c.page_content),
            "has_misinformation": False,
            "CARDS_code": None,
            "CARDS_category": None,
            "rebuttal": None,
        }
        for i, c in enumerate(
            get_base_chunks(cleaned, chunk_size=1000, chunk_overlap=0)
        )
    ]

    logger.info(f"Chunking complete. Total chunks: {len(chunks)}")

    return {"chunks": chunks}


# Changed to async def to handle the await calls natively
async def transcribe_pdf(file_obj, progress=gr.Progress()):
    if not file_obj:
        yield "Please upload a PDF.", {}
        return

    try:
        progress(0, desc="Extracting PDF text...")
        yield "<p>Transcribing document...</p>", {}

        encoded_pdf = encode_pdf_to_base64(file_obj.name)
        message = HumanMessage(
            content=[
                {"type": "text", "text": transcription_prompt},
                {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
            ]
        )

        raw_markdown = google_llm.invoke([message]).content

        initial_state = create_document_state(raw_markdown)

        # Call the async analyzer directly with await
        final_state = await analyze_chunks(initial_state, progress=progress)

        progress(0.9, desc="Rendering...")
        # Return both the HTML for the UI and the final_state for the gr.State
        yield render_document(final_state), final_state

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        yield f"Error: {str(e)}", {}


async def process_url(url, progress=gr.Progress()):
    if not url or not url.startswith("http"):
        yield "Please enter a valid URL."
        return

    # 1 download
    logger.info(f"Processing {url}")
    html = trafilatura.fetch_url(url)

    # 2 extract main article as HTML
    article_html = trafilatura.extract(
        html,
        output_format="html",
        include_links=True,
        include_tables=True,
        include_comments=False,
    )
    if article_html and "request unsuccessful" not in article_html.lower():
        # 3 clean unwanted links but keep citations
        soup = BeautifulSoup(article_html, "html.parser")

        for a in soup.find_all("a"):
            href = a.get("href", "")

            # keep footnotes and references
            if href.startswith("#") or "footnote" in href:
                continue

            # unwrap navigation links
            if not href.startswith("http"):
                a.unwrap()

        clean_html = str(soup)

        # 4 convert to markdown (high fidelity)
        raw_markdown = pypandoc.convert_text(
            clean_html,
            "markdown",
            format="html",
        )
        logger.info(f"Received markdown {raw_markdown[:200]}")
        initial_state = create_document_state(raw_markdown)

        final_state = await analyze_chunks(initial_state, progress=progress)

        progress(0.9, desc="Rendering...")
        yield render_document(final_state), final_state

    else:
        yield "Request unsuccessful, failed to extract article content"


with gr.Blocks() as app:
    # doc_state is useful if you want to download the results later
    doc_state = gr.State({"chunks": []})

    gr.Markdown("## Fighting Harmful Online Communication (fhoc)")

    with gr.Tabs():
        with gr.TabItem("Upload PDF"):
            input_file = gr.File(label="Upload PDF", file_types=[".pdf"])
            file_submit_btn = gr.Button("Analyze", variant="primary")
        with gr.TabItem("Enter URL"):
            url_input = gr.Textbox(
                label="Enter URL", placeholder="https://example.com/article"
            )
            url_submit_btn = gr.Button("Analyze", variant="primary")
        # ... (URL tab stays the same) ...

        output_html = gr.HTML(label="Analysis Results")

    # Correct wiring: functions return (HTML, State)
    file_submit_btn.click(
        fn=transcribe_pdf, inputs=[input_file], outputs=[output_html, doc_state]
    )

    url_submit_btn.click(
        fn=process_url, inputs=[url_input], outputs=[output_html, doc_state]
    )

if __name__ == "__main__":
    app.launch(
        css=custom_css, theme=gr.themes.Monochrome()
    )  # Use 127.0.0.1 instead of 0.0.0.0 for Safari
