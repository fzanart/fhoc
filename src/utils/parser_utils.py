import re
import base64


def clean_markdown(text):
    """
    Removes the ```markdown and ``` wrappers that LLMs often include.
    """
    # Remove leading ```markdown or ```
    text = re.sub(r"^```(?:markdown)?\n?", "", text, flags=re.IGNORECASE)
    # Remove trailing ```
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def encode_pdf_to_base64(file_path):
    """Helper to convert local file to base64 string."""
    with open(file_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode("utf-8")
    return encoded_string
