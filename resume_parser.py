"""
Extracts plain text from an uploaded resume (PDF or TXT).
Kept intentionally simple: production resume parsers do structured
field extraction (skills/education/experience as separate fields),
but for this project we extract raw text and let the LLM do the
structured reasoning over it -- that's a good demonstration of using
an LLM instead of brittle regex rules.
"""

import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF file given as raw bytes."""
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks).strip()


def extract_text_from_upload(uploaded_file) -> str:
    """
    Given a Streamlit UploadedFile object, return its text content
    regardless of whether it's a .pdf or .txt file.
    """
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    else:
        # Treat anything else as plain text
        return file_bytes.decode("utf-8", errors="ignore").strip()
