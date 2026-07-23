import pytesseract
from PIL import Image

# Path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\sibabalompongwane\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)


def extract_text_from_image(image_file):
    """
    Extract text from an image using OCR.
    """

    image = Image.open(image_file)

    text = pytesseract.image_to_string(image)

    return text