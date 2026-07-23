import fitz  # PyMuPDF


def extract_pdf_text(uploaded_file):
    """
    Reads an uploaded PDF file and returns all text.
    """

    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    text = ""

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text