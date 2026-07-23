from modules.ocr_engine import extract_text_from_image


def process_image(uploaded_file):
    """
    Processes an uploaded image and returns extracted text.
    """

    extracted_text = extract_text_from_image(uploaded_file)

    return extracted_text