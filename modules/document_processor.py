from modules.pdf_reader import extract_pdf_text
from modules.docx_reader import extract_docx_text
from modules.image_processor import process_image
from modules.text_cleaner import clean_text


def process_document(uploaded_file):
    """
    Reads an uploaded document, extracts its text,
    cleans it, and returns the cleaned text.
    """

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):

        text = extract_pdf_text(uploaded_file)

    elif filename.endswith(".docx"):

        text = extract_docx_text(uploaded_file)

    elif (
        filename.endswith(".png")
        or filename.endswith(".jpg")
        or filename.endswith(".jpeg")
    ):

        text = process_image(uploaded_file)

    elif filename.endswith(".txt"):

        text = uploaded_file.read().decode("utf-8")

    else:

        raise ValueError(
            "Unsupported file type."
        )

    text = clean_text(text)

    return text