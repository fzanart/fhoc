"""Context-Enriched Chunking"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


def get_context_enriched_chunks(
    document_text,
    llm,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
):

    base_chunks = get_base_chunks(document_text, chunk_size, chunk_overlap)

    document_overview = document_summary(document_text, llm)

    enriched_documents = []
    for i, chunk in enumerate(base_chunks):
        print(f"Processing chunk {i+1}/{len(base_chunks)}")

        doc = create_enriched_document(
            document_overview,
            chunk,
            i,
            llm,
        )

        enriched_documents.append(doc)

    return enriched_documents


def create_enriched_document(
    document_overview,
    chunk,
    chunk_id,
    llm,
):

    metadata = {
        "chunk_id": chunk_id,
        "chunk_length": len(chunk.page_content),
        "start_index": chunk.metadata.get("start_index", 0),
        "chunk": chunk.page_content,
        "document_summary": document_overview,
    }

    chunk_summary = summarize_context(document_overview, chunk.page_content, llm)

    metadata["chunk_summary"] = chunk_summary

    return Document(page_content=chunk.page_content, metadata=metadata)


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


def get_base_chunks(document_text, chunk_size, chunk_overlap):

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", " "],  # Paragraph → Line → Sentence → Word
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
        strip_whitespace=False,
    )

    base_chunks = text_splitter.create_documents([document_text])

    return base_chunks
