import json
from pathlib import Path


def build_knowledge(
    structured_text,
    original_filename,
    project_name
):
    """
    Builds and saves a structured knowledge base
    from an educational document.
    """

    knowledge = {

        "document": original_filename,

        "modules": [],

        "learning_outcomes": [],

        "assessment_criteria": [],

        "knowledge_requirements": [],

        "practical_activities": [],

        "workplace_activities": []

    }

    current_section = None

    for line in structured_text.splitlines():

        line = line.strip()

        if not line:
            continue

        upper = line.upper()

        # ----------------------------
        # MODULES
        # ----------------------------

        if (
            upper.startswith("MODULE")
            or upper.startswith("KNOWLEDGE MODULE")
            or upper.startswith("PRACTICAL MODULE")
            or upper.startswith("WORK EXPERIENCE MODULE")
        ):

            knowledge["modules"].append(line)

            current_section = None

            continue

        # ----------------------------
        # SECTION HEADINGS
        # ----------------------------

        if upper == "LEARNING OUTCOMES":

            current_section = "learning_outcomes"
            continue

        if upper == "ASSESSMENT CRITERIA":

            current_section = "assessment_criteria"
            continue

        if upper == "KNOWLEDGE REQUIREMENTS":

            current_section = "knowledge_requirements"
            continue

        if upper == "PRACTICAL ACTIVITIES":

            current_section = "practical_activities"
            continue

        if upper == "WORKPLACE ACTIVITIES":

            current_section = "workplace_activities"
            continue

        # Ignore divider lines

        if (
            line.startswith("=")
            or line.startswith("-")
        ):
            continue

        # Store content

        if current_section:

            knowledge[current_section].append(line)

    # ----------------------------
    # SAVE JSON
    # ----------------------------

    project_folder = Path("projects") / project_name

    knowledge_folder = project_folder / "knowledge"

    knowledge_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        knowledge_folder /
        (Path(original_filename).stem + ".json")
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            knowledge,
            file,
            indent=4,
            ensure_ascii=False
        )

    return knowledge