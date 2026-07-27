import os
import json


def generate_lesson_plan(project_path):
    """
    Reads extracted text files from the project
    and prepares them for AI processing.
    """

    extracted_folder = os.path.join(project_path, "extracted_text")

    combined_text = ""

    if not os.path.exists(extracted_folder):
        return None

    for filename in os.listdir(extracted_folder):

        if filename.endswith(".txt"):

            filepath = os.path.join(extracted_folder, filename)

            with open(filepath, "r", encoding="utf-8") as file:
                combined_text += file.read()
                combined_text += "\n\n"

    return combined_text