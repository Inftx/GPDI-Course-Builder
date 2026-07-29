from modules.pdf_reader import extract_pdf_text
from modules.docx_reader import extract_docx_text
from modules.image_processor import process_image

from modules.text_cleaner import clean_text
from modules.document_structurer import structure_document


def process_document(uploaded_file):
    """
    Processes an uploaded document and returns:

    - Raw extracted text
    - Cleaned text
    - Structured text
    """

    filename = uploaded_file.name.lower()

    # -----------------------------
    # Extract Raw Text
    # -----------------------------

    if filename.endswith(".pdf"):

        raw_text = extract_pdf_text(uploaded_file)

    elif filename.endswith(".docx"):

        raw_text = extract_docx_text(uploaded_file)

    elif filename.endswith((".png", ".jpg", ".jpeg")):

        raw_text = process_image(uploaded_file)

    elif filename.endswith(".txt"):

        raw_text = uploaded_file.read().decode("utf-8")

    else:

        raise ValueError("Unsupported file type.")

    # -----------------------------
    # Clean Text
    # -----------------------------

    cleaned_text = clean_text(raw_text)

    # -----------------------------
    # Structure Text
    # -----------------------------

    structured_text = structure_document(cleaned_text)

    return {
        "raw": raw_text,
        "clean": cleaned_text,
        "structured": structured_text
    }