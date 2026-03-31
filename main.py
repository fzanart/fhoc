"""
Gradio interface for fighting harmful online communication (fhoc).
"""

import asyncio
import logging
from pathlib import Path
import gradio as gr
import trafilatura
from bs4 import BeautifulSoup
import pypandoc
from langchain_core.messages import HumanMessage
from transformers import pipeline
from src.llm.llms import google_llm
from src.utils.parser_utils import clean_markdown, encode_pdf_to_base64
from src.utils.chunking import get_base_chunks
from src.api.cards import classify_text
from src.api.rebuttal import RebuttalStructure
from src.api.narrative import analyze_components, render_narrative_html
from src.api.debunk import render_debunk_html
from src.api.debunk_summary import generate_debunk_summary


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


# ---------------------------------------------------------------------------
# Extraction helpers — input → raw markdown
# ---------------------------------------------------------------------------


def _markdown_from_url(url: str) -> str:
    html = trafilatura.fetch_url(url)
    article_html = trafilatura.extract(
        html,
        output_format="html",
        include_links=True,
        include_tables=True,
        include_comments=False,
    )
    if not article_html or "request unsuccessful" in article_html.lower():
        raise ValueError("Failed to extract article content from URL.")

    soup = BeautifulSoup(article_html, "html.parser")
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href.startswith("#") or "footnote" in href:
            continue
        if not href.startswith("http"):
            a.unwrap()

    return pypandoc.convert_text(str(soup), "markdown", format="html")


def _markdown_from_pdf(file_obj) -> str:
    encoded_pdf = encode_pdf_to_base64(file_obj.name)
    message = HumanMessage(
        content=[
            {"type": "text", "text": transcription_prompt},
            {
                "type": "file",
                "file": {
                    "filename": Path(file_obj.name).name,
                    "file_data": f"data:application/pdf;base64,{encoded_pdf}",
                },
            },
        ]
    )
    return google_llm.invoke([message]).content


def _state_from_markdown(raw_markdown: str) -> dict:
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


# ---------------------------------------------------------------------------
# Analysis — shared across both input types
# ---------------------------------------------------------------------------


async def _debunk(state: dict, progress: gr.Progress) -> tuple[str, dict]:
    chunks = [{**c} for c in state["chunks"]]
    by_id = {c["id"]: c for c in chunks}
    zeros = ("0", "0.0", 0, 0.0, "0_0_0", "<0_0_0>")

    progress(0.2, desc="Classifying claims...")
    resps = await asyncio.gather(*[asyncio.to_thread(classify_text, c["text"]) for c in chunks])

    misinfo_chunks = []
    for chunk, resp in zip(chunks, resps):
        logger.info(f"Chunk {chunk['id']} classified: {resp.category}")
        chunk["CARDS_code"] = resp.category
        chunk["CARDS_category"] = resp.description
        if resp.category not in zeros:
            chunk["has_misinformation"] = True
            misinfo_chunks.append(chunk["id"])

    full_text = "\n\n".join(c["text"] for c in chunks)

    if misinfo_chunks:
        texts = [by_id[i]["text"] for i in misinfo_chunks]
        logger.info(f"Detecting fallacies for {len(texts)} chunks")
        labels = await asyncio.to_thread(pipe, texts)
        for chunk_id, result in zip(misinfo_chunks, labels):
            by_id[chunk_id]["fallacy"] = result["label"]

        flicc_labels = list(dict.fromkeys(by_id[i]["fallacy"] for i in misinfo_chunks if by_id[i].get("fallacy")))
        cards_cats = list(dict.fromkeys(f'{by_id[i]["CARDS_code"]} — {by_id[i]["CARDS_category"]}' for i in misinfo_chunks))

        progress(0.5, desc="Generating rebuttals...")
        rebuttal_gen = RebuttalStructure()
        coros = [rebuttal_gen.run(by_id[i]["text"], by_id[i]["fallacy"]) for i in misinfo_chunks]
        *rebuttal_results, debunk_summary = await asyncio.gather(
            *coros,
            generate_debunk_summary(full_text, flicc_labels, cards_cats),
        )
        for chunk_id, rebuttal in zip(misinfo_chunks, rebuttal_results):
            by_id[chunk_id]["rebuttal"] = rebuttal
    else:
        debunk_summary = await generate_debunk_summary(full_text, [], [])

    final_state = {"chunks": list(by_id.values()), "_debunk_summary": debunk_summary}
    return render_debunk_html(final_state), final_state


async def _narrative(state: dict, progress: gr.Progress) -> tuple[str, dict]:
    progress(0.5, desc="Analyzing narrative framing...")
    text = "\n\n".join(c["text"] for c in state["chunks"])
    result = await analyze_components(text)
    return render_narrative_html(result), state


# ---------------------------------------------------------------------------
# Gradio handlers — one per (input type × analysis type)
# ---------------------------------------------------------------------------


def _make_handler(get_markdown, analysis_fn, analysis_key):
    """
    analysis_key: "debunk" | "narrative" — identifies which result to cache.
    """

    async def handler(source, state, progress=gr.Progress()):
        if not source:
            yield "Please provide an input.", state
            return
        try:
            source_key = source if isinstance(source, str) else source.name

            # Source changed — reset everything
            if state.get("_source") != source_key:
                logger.info(f"New source detected, resetting state: {source_key}")
                progress(0, desc="Extracting text...")
                yield "<p>Extracting text...</p>", state
                raw_markdown = await asyncio.to_thread(get_markdown, source)
                state = _state_from_markdown(raw_markdown)
                state["_source"] = source_key
                state["_cache"] = {}  # fresh cache for both analyses

            # Return cached result if available
            if analysis_key in state.get("_cache", {}):
                logger.info(f"Returning cached {analysis_key} result.")
                yield state["_cache"][analysis_key], state
                return

            # Run analysis and cache result
            progress(0.3, desc="Running analysis...")
            html, final_state = await analysis_fn(state, progress)
            final_state.setdefault("_cache", {})[analysis_key] = html
            progress(0.9, desc="Rendering...")
            yield html, final_state

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            yield f"<p>Error: {e}</p>", state

    return handler


pdf_debunk_fn = _make_handler(_markdown_from_pdf, _debunk, "debunk")
pdf_narrative_fn = _make_handler(_markdown_from_pdf, _narrative, "narrative")
url_debunk_fn = _make_handler(_markdown_from_url, _debunk, "debunk")
url_narrative_fn = _make_handler(_markdown_from_url, _narrative, "narrative")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

with gr.Blocks() as app:

    doc_state = gr.State({"chunks": []})
    gr.Markdown("## Fighting Harmful Online Communication (fhoc)")

    with gr.Tabs():

        with gr.TabItem("Upload PDF"):
            input_file = gr.File(label="Upload PDF", file_types=[".pdf"])
            with gr.Row():
                pdf_debunk_btn = gr.Button("🔍 Claim Debunking", variant="primary")
                pdf_narrative_btn = gr.Button(
                    "📰 Narrative Framing", variant="secondary"
                )
            output_pdf = gr.HTML(label="Analysis Results")

        with gr.TabItem("Enter URL"):
            url_input = gr.Textbox(
                label="Enter URL", placeholder="https://example.com/article"
            )
            with gr.Row():
                url_debunk_btn = gr.Button("🔍 Claim Debunking", variant="primary")
                url_narrative_btn = gr.Button(
                    "📰 Narrative Framing", variant="secondary"
                )
            output_url = gr.HTML(label="Analysis Results")

    pdf_debunk_btn.click(
        fn=pdf_debunk_fn,
        inputs=[input_file, doc_state],
        outputs=[output_pdf, doc_state],
    )
    pdf_narrative_btn.click(
        fn=pdf_narrative_fn,
        inputs=[input_file, doc_state],
        outputs=[output_pdf, doc_state],
    )
    url_debunk_btn.click(
        fn=url_debunk_fn,
        inputs=[url_input, doc_state],
        outputs=[output_url, doc_state],
    )
    url_narrative_btn.click(
        fn=url_narrative_fn,
        inputs=[url_input, doc_state],
        outputs=[output_url, doc_state],
    )


if __name__ == "__main__":
    app.launch(css=custom_css, theme=gr.themes.Monochrome())
