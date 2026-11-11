import os
import shutil
from pathlib import Path

import pytesseract
from PIL import Image


def configure_tesseract():
    """Locate and configure the Tesseract OCR executable."""

    candidates = [
        shutil.which("tesseract"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return str(candidate)

    return None


TESSERACT_PATH = configure_tesseract()


def extract_text_from_image(image_file):
    """Extract text from an image using Tesseract OCR."""

    if not TESSERACT_PATH:
        raise FileNotFoundError(
            "Tesseract OCR executable was not found. "
            "Please install Tesseract OCR."
        )

    image = Image.open(image_file).convert("RGB")

    text = pytesseract.image_to_string(image)

    return text