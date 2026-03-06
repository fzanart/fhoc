"""
Simplified Gradio interface for misinformation detection.
This is the minimal version for quick prototyping.
"""

import asyncio
import logging
import copy
from pathlib import Path
import gradio as gr
from langchain_core.messages import HumanMessage
from src.llm.llms import google_llm, google_llm_with_url_context
from src.utils.parser_utils import clean_markdown, encode_pdf_to_base64
from src.utils.chunking import get_base_chunks
from src.api.apis import classify_text
from src.api.rebuttal import RebuttalStructure


transcription_prompt = Path("./src/prompts/md_transcript.md").read_text(
    encoding="utf-8"
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def analyze_chunks(prev_state):
    chunks = copy.deepcopy(prev_state["chunks"])
    by_id = {c["id"]: c for c in chunks}

    async def classify(chunk):
        resp = await asyncio.to_thread(classify_text, chunk["text"])
        return chunk["id"], resp

    results = await asyncio.gather(*[classify(c) for c in chunks])
    rebuttal_gen = RebuttalStructure()
    rebuttal_jobs = []

    for chunk_id, resp in results:
        chunk = by_id[chunk_id]
        chunk["CARDS_code"] = resp.category
        chunk["CARDS_category"] = resp.description
        if resp.category != "0":
            chunk["has_misinformation"] = True
            rebuttal_jobs.append(
                (chunk_id, asyncio.to_thread(rebuttal_gen.run, chunk["text"]))
            )
    rebuttals = await asyncio.gather(*[job for _, job in rebuttal_jobs])

    for (chunk_id, _), rebuttal in zip(rebuttal_jobs, rebuttals):
        by_id[chunk_id]["rebuttal"] = rebuttal

    marked_markdown = prev_state["raw_markdown"]
    insertions = []
    used_positions = set()

    for chunk in by_id.values():
        if "rebuttal" in chunk:
            start_idx = 0
            while (idx := marked_markdown.find(chunk["text"], start_idx)) != -1:
                end_pos = idx + len(chunk["text"])
                if end_pos not in used_positions:
                    insertions.append((end_pos, chunk["id"]))
                    used_positions.add(end_pos)
                    break
                start_idx = idx + 1

    for pos, c_id in sorted(insertions, key=lambda x: x[0], reverse=True):
        marked_markdown = (
            f"{marked_markdown[:pos]} [[REBUTTAL:{c_id}]] {marked_markdown[pos:]}"
        )
    return {
        "raw_markdown": marked_markdown,
        "chunks": list(by_id.values()),
    }


def render_document(state):
    chunks = [
        {
            "id": c["id"],
            "text": c["text"],
            "start": c["start"],
            "end": c["end"],
            "has_misinformation": c.get("has_misinformation", False),
            "rebuttal": c.get("rebuttal", ""),
            "CARDS_category": c.get("CARDS_category", ""),
        }
        for c in state["chunks"]
    ]

    for i, chunk in enumerate(chunks):
        chunk["overlap"] = 0 if i == 0 else chunks[i - 1]["end"] - chunk["start"]

    doc_spans = ""
    annotations = ""
    n = 1

    for chunk in chunks:
        if chunk["has_misinformation"]:
            doc_spans += (
                f'<span style="background:#ffe0b2; border-bottom:2px solid orange;">'
                f'{chunk["text"]}'
                f'<sup style="color:orange; font-weight:bold;">[{n}]</sup>'
                f"</span>"
            )
            annotations += (
                f'<div style="border-left:3px solid orange; padding:8px 12px; margin-bottom:12px;'
                f'background:#333; color:white; border-radius:4px; font-size:0.85em;">'
                f'<strong style="color:orange;">[{n}] {chunk["CARDS_category"]}</strong><br>{chunk["rebuttal"]}'
                f"</div>"
            )
            n += 1
        else:
            doc_spans += f'<span>{chunk["text"]}</span>'

    doc_html = f'<div style="font-family:Georgia; line-height:1.8; color:#111;">{doc_spans}</div>'
    ann_html = (
        f'<div style="font-family:Georgia;">{annotations}</div>' if annotations else ""
    )

    return (
        f'<div style="display:flex; gap:24px;">'
        f'  <div style="flex:3">{doc_html}</div>'
        f'  <div style="flex:1">{ann_html}</div>'
        f"</div>"
    )


def stream_llm_markdown(message, prev_state, llm):
    """Common logic to stream from Gemini and yield markdown updates."""
    markdown = ""
    for chunk in llm.stream([message]):
        markdown += chunk.content
        yield markdown, prev_state

    # After streaming is done, final state processing
    new_state = create_document_state(markdown)
    yield new_state["raw_markdown"], new_state


def create_document_state(raw_markdown):
    """Common logic to clean markdown and create the doc_state dictionary."""
    cleaned = clean_markdown(raw_markdown)

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
            get_base_chunks(cleaned, chunk_size=1000, chunk_overlap=200)
        )
    ]

    return {
        "raw_markdown": cleaned,
        "chunks": chunks,
    }


def transcribe_pdf(file_obj, prev_state):
    if not file_obj:
        yield "Please upload a PDF.", prev_state
        return

    try:
        file_size = Path(file_obj.name).stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB
            yield "File is too large. Please upload a PDF smaller than 10MB.", prev_state
            return

        encoded_pdf = encode_pdf_to_base64(file_obj.name)

        message = HumanMessage(
            content=[
                {"type": "text", "text": transcription_prompt},
                {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
            ]
        )

        yield from stream_llm_markdown(message, prev_state, google_llm)
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        yield "An error occurred while processing the PDF. Please try again.", prev_state


def process_url(url, prev_state):
    if not url or not url.startswith("http"):
        yield "Please enter a valid URL.", prev_state
        return

    message = HumanMessage(
        content=[
            {"type": "text", "text": f"{transcription_prompt}\n\nURL: {url}"},
        ]
    )

    yield from stream_llm_markdown(message, prev_state, google_llm_with_url_context)


with gr.Blocks() as app:

    doc_state = gr.State(
        {
            "raw_markdown": "",
            "chunks": [],
        }
    )

    gr.Markdown("## Fighting Harmful Online Communication (fhoc)")
    gr.Markdown("An AI-based tool to detect and counter climate misinformation")

    with gr.Tabs():
        with gr.TabItem("Upload PDF"):
            input_file = gr.File(label="Upload PDF file", file_types=[".pdf"])
            file_submit_btn = gr.Button("Analyze", variant="primary")
        with gr.TabItem("Enter URL"):
            url_input = gr.Textbox(
                label="Enter URL", placeholder="https://example.com/article"
            )
            url_submit_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            output_text = gr.HTML(label="Analysis Results")

    # --- Path 1: PDF Upload ---
    file_submit_btn.click(
        fn=transcribe_pdf,
        inputs=[input_file, doc_state],
        outputs=[output_text, doc_state],
    ).then(
        fn=analyze_chunks,
        inputs=doc_state,
        outputs=doc_state,
    ).then(
        fn=render_document,
        inputs=doc_state,
        outputs=output_text,
    )

    # --- Path 2: URL Input ---
    url_submit_btn.click(
        fn=process_url,
        inputs=[url_input, doc_state],
        outputs=[output_text, doc_state],
    ).then(
        fn=analyze_chunks,
        inputs=doc_state,
        outputs=doc_state,
    ).then(
        fn=render_document,
        inputs=doc_state,
        outputs=output_text,
    )

if __name__ == "__main__":
    app.launch()  # Use 127.0.0.1 instead of 0.0.0.0 for Safari
