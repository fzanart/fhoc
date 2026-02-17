"""
Simplified Gradio interface for misinformation detection.
This is the minimal version for quick prototyping.
"""

import logging
from pathlib import Path
import gradio as gr
from langchain_core.messages import HumanMessage
from src.llm.llms import google_llm
from src.utils.parser_utils import clean_markdown, encode_pdf_to_base64
from src.utils.chunking import get_base_chunks
from src.utils.annotation_rendering import (
    calculate_coverage,
    create_end_markers,
    highlight_text,
    create_layout,
)
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


def analyze_chunks(prev_state):
    chunks = [c.copy() for c in prev_state["chunks"]]
    rebuttal_gen = RebuttalStructure()

    for chunk in chunks:
        resp = classify_text(chunk["text"])
        chunk["CARDS_code"] = resp.category
        chunk["CARDS_category"] = resp.description

        if resp.category != "0":
            chunk["has_misinformation"] = True
            chunk["rebuttal"] = rebuttal_gen.run(chunk["text"])

    return {
        "raw_markdown": prev_state["raw_markdown"],
        "chunks": chunks,
    }


def render_document(state):
    misleading = [c for c in state["chunks"] if c["has_misinformation"]]

    coverage = calculate_coverage(misleading)
    end_markers = create_end_markers(misleading)

    annotated = highlight_text(state["raw_markdown"], coverage, end_markers)

    return create_layout(annotated, misleading)


def transcribe_pdf(file_obj, prev_state):
    if not file_obj:
        yield "Please upload a PDF."
        return

    encoded_pdf = encode_pdf_to_base64(file_obj.name)

    message = HumanMessage(
        content=[
            {"type": "text", "text": transcription_prompt},
            {"type": "media", "mime_type": "application/pdf", "data": encoded_pdf},
        ]
    )

    markdown = ""
    for chunk in google_llm.stream([message]):
        markdown += chunk.content
        yield markdown, prev_state

    cleaned = clean_markdown(markdown)

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

    new_state = {
        "raw_markdown": cleaned,
        "chunks": chunks,
    }

    yield cleaned, new_state


with gr.Blocks() as demo:

    doc_state = gr.State(
        {
            "raw_markdown": "",
            "chunks": [],
        }
    )

    gr.Markdown("## Gemini Multimodal Chat (LangChain + Gradio)")

    with gr.Row():
        with gr.Row():
            input_file = gr.File(label="Upload PDF file", file_types=[".pdf"])
            submit_btn = gr.Button("Analyze", variant="primary")

        with gr.Row():
            output_text = gr.Markdown(label="Gemini's Response", line_breaks=True)

    submit_btn.click(
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

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",  # Use 127.0.0.1 instead of 0.0.0.0 for Safari
        server_port=7860,
    )
