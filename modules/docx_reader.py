from docx import Document


def extract_docx_text(uploaded_file):
    """
    Reads an uploaded DOCX file and returns all text.
    """

    document = Document(uploaded_file)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text