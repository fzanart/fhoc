"""Context-Enriched Chunking"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def get_context_enriched_chunks(
    document_text,
    llm,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    window_size: int = 2,
):

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],  # Paragraph → Line → Sentence → Word
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    base_chunks = text_splitter.split_text(document_text)

    document_overview = document_summary(document_text, llm)

    enriched_documents = []
    for i, chunk in enumerate(base_chunks):
        print(f"Processing chunk {i+1}/{len(base_chunks)}")

        context_chunks, window_start, window_end = get_context_window(
            base_chunks, i, window_size
        )

        doc = create_enriched_document(
            document_overview,
            chunk,
            context_chunks,
            i,
            len(base_chunks),
            window_start,
            window_end,
            llm,
        )

        enriched_documents.append(doc)

    return enriched_documents


def create_enriched_document(
    document_overview,
    chunk,
    context_chunks,
    chunk_id,
    total_chunks,
    window_start,
    window_end,
    llm,
):
    context_text = " ".join(context_chunks)

    metadata = {
        "chunk_id": chunk_id,
        "total_chunks": total_chunks,
        "chunk_size": len(chunk),
        "window_start_idx": window_start,
        "window_end_idx": window_end - 1,
        "has_context": len(context_chunks) > 0,
        "chunk": chunk,
        "document_summary": document_overview,
    }

    chunk_summary = summarize_context(document_overview, context_text, llm)

    metadata["chunk_summary"] = chunk_summary

    return Document(page_content=chunk, metadata=metadata)


def document_summary(document_text, llm):
    prompt = PromptTemplate.from_template(
        "Summarize the main topic and purpose of this document in 2-3 sentences: "
        "\n\n"
        "Document:"
        "{document}"
        "\n\n"
        "Summary:"
    )
    chain = prompt | llm
    # roughly 1 long essay = 2k words; 1 word ~ 5 characters
    # limit to first 10k characters for cost/speed processing.
    response = chain.invoke({"document": document_text[:10000]})
    return response.content


def summarize_context(document_overview, context_text, llm):
    prompt = PromptTemplate.from_template(
        "You are an expert document analyst tasked with creating concise, clear summaries of text passages. "
        "Your summaries help readers quickly grasp the core message of each section.\n\n"
        "Overall Document Context: {global_summary}\n\n"
        "Instructions:\n"
        "- Provide a brief 1-2 sentence summary that states the main claim or idea expressed in the text below\n"
        "- Begin with a concrete subject (e.g., a concept, actor, or phenomenon)\n"
        "- Avoid meta-phrases such as 'this snippet', 'this excerpt', 'the text', or similar references\n"
        "- Focus on what is being discussed, not that something is being discussed\n\n"
        "Text: {text}\n\n"
        "Summary:"
    )
    chain = prompt | llm
    response = chain.invoke({"global_summary": document_overview, "text": context_text})
    return response.content


def get_context_window(base_chunks, current_index, window_size):
    window_start = max(0, current_index - window_size)
    window_end = min(len(base_chunks), current_index + window_size + 1)

    window = base_chunks[window_start:window_end]
    context_chunks = [
        chunk for j, chunk in enumerate(window) if j != current_index - window_start
    ]

    return context_chunks, window_start, window_end
