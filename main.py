"""
Simplified Gradio interface for misinformation detection.
This is the minimal version for quick prototyping.
"""

import logging
import pprint
from pathlib import Path
import gradio as gr
from src.utils.parser import MarkdownConverter
from src.utils.chunking import get_base_chunks
from src.api.apis import classify_text
from src.api.rebuttal import RebuttalStructure

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def analyze_document(pdf_file, url_text):
    """
    Simple analysis function that processes PDF or URL input.

    Returns formatted HTML with highlighted misinformation and rebuttals.
    """
    # Step 1: Convert to markdown
    md = MarkdownConverter()

    if pdf_file is not None:
        logger.info(f"📄 Processing PDF file: {pdf_file}")
        document = md.run(pdf_file)
        source = Path(pdf_file).name
    elif url_text and url_text.strip():
        logger.info(f"🔗 Processing URL: {url_text}")
        document = md.run(url_text)
        source = url_text
    else:
        return "<p style='color: red;'>❌ Please provide a PDF or URL</p>"

    # Step 2: Chunk the document
    chunks = get_base_chunks(document, chunk_size=1000, chunk_overlap=200)
    logger.info(f"✅ Created {len(chunks)} chunks")
    logger.info(f"✅ First chunk: {pprint.pformat(chunks[0], indent=4)}")

    # Step 3: Classify chunks
    # Handle both Document objects and dicts
    responses = []
    for chunk in chunks:
        # Extract text from Document object or dict
        if hasattr(chunk, "page_content"):
            # LangChain Document object
            chunk_text = chunk.page_content
        elif isinstance(chunk, dict):
            # Dictionary format
            chunk_text = chunk.get("metadata", {}).get("chunk") or chunk.get("text", "")
        else:
            # Fallback: try to convert to string
            chunk_text = str(chunk)

        if chunk_text:
            responses.append(classify_text(chunk_text))

    # Step 4: Keep only positive misinformation detections
    positive_responses = [r for r in responses if r.category != "0"]

    # If no misinformation found
    if not positive_responses:
        return f"""
        <div style='padding: 30px; background: #d4edda; border-radius: 8px; text-align: center;'>
            <h2>✅ No Misinformation Detected</h2>
            <p>Source: {source}</p>
        </div>
        """

    # Step 5: Generate rebuttals
    rebuttal_gen = RebuttalStructure()
    rebuttals = [rebuttal_gen.run(misinfo) for misinfo in positive_responses]

    # Step 6: Build output HTML
    output = f"""
    <div style='max-width: 900px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;'>
        <h2>📋 Misinformation Analysis</h2>
        <p><strong>Source:</strong> {source}</p>
        <p><strong>Issues Found:</strong> {len(positive_responses)} out of {len(chunks)} sections</p>
        <hr>
    """

    # Map responses to chunks
    response_index = 0
    for i, chunk in enumerate(chunks):
        # Extract text from Document object or dict
        if hasattr(chunk, "page_content"):
            chunk_text = chunk.page_content
        elif isinstance(chunk, dict):
            chunk_text = chunk.get("metadata", {}).get("chunk") or chunk.get("text", "")
        else:
            chunk_text = str(chunk)

        # Check if this chunk has misinformation
        if i < len(responses) and responses[i].category != "0":
            # Highlighted section with rebuttal
            output += f"""
            <div style='background: #fff3cd; padding: 20px; margin: 20px 0; border-left: 4px solid #ff9800; border-radius: 4px;'>
                <p style='margin: 0; font-size: 16px;'>{chunk_text}</p>
                <div style='margin-top: 15px; padding: 15px; background: white; border-left: 3px solid #2196F3; border-radius: 4px;'>
                    <strong style='color: #2196F3;'>🔍 Fact Check:</strong>
                    <p style='margin: 5px 0 0 0;'>{rebuttals[response_index]}</p>
                </div>
            </div>
            """
            response_index += 1
        else:
            # Normal section
            output += f"""
            <div style='padding: 15px; margin: 15px 0; background: #f5f5f5; border-radius: 4px;'>
                <p style='margin: 0;'>{chunk_text}</p>
            </div>
            """

    output += "</div>"
    return output


# Create simple Gradio interface
demo = gr.Interface(
    fn=analyze_document,
    inputs=[
        gr.File(label="📄 Upload PDF (optional)", file_types=[".pdf"]),
        gr.Textbox(
            label="🔗 Or Enter URL (optional)",
            placeholder="https://example.com/article",
        ),
    ],
    outputs=gr.HTML(label="Analysis Results"),
    title="🔍 Misinformation Detector",
    description="Upload a PDF or enter a URL to detect and fact-check potential misinformation.",
)


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",  # Use 127.0.0.1 instead of 0.0.0.0 for Safari
        server_port=7860,
    )
