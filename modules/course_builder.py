import json
from pathlib import Path

from services.rag.chunker import chunk_document
from services.rag.indexer import build_index
from services.rag.storage import save_index


def build_course(project_name):
    """
    Combines all knowledge JSON files in a project
    into a single course knowledge base.
    """

    project_folder = Path("projects") / project_name

    knowledge_folder = project_folder / "knowledge"

    course = {
        "project": project_name,
        "documents": [],
        "modules": [],
        "learning_outcomes": [],
        "assessment_criteria": [],
        "knowledge_requirements": [],
        "practical_activities": [],
        "workplace_activities": []
    }

    if not knowledge_folder.exists():
        return course

    for file in knowledge_folder.glob("*.json"):

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            knowledge = json.load(f)

        course["documents"].append(
            knowledge["document"]
        )

        course["modules"].extend(
            knowledge["modules"]
        )

        course["learning_outcomes"].extend(
            knowledge["learning_outcomes"]
        )

        course["assessment_criteria"].extend(
            knowledge["assessment_criteria"]
        )

        course["knowledge_requirements"].extend(
            knowledge["knowledge_requirements"]
        )

        course["practical_activities"].extend(
            knowledge["practical_activities"]
        )

        course["workplace_activities"].extend(
            knowledge["workplace_activities"]
        )

    output = project_folder / "course.json"

    with open(
        output,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            course,
            file,
            indent=4,
            ensure_ascii=False
        )

    knowledge_chunks = chunk_document(
        "\n\n".join(
            [
                "Course Documents\n" + "\n".join(course["documents"]),
                "\n".join(course["modules"]),
                "Learning Outcomes\n" + "\n".join(course["learning_outcomes"]),
                "Assessment Criteria\n" + "\n".join(course["assessment_criteria"]),
                "Knowledge Requirements\n" + "\n".join(course["knowledge_requirements"]),
                "Practical Activities\n" + "\n".join(course["practical_activities"]),
                "Workplace Activities\n" + "\n".join(course["workplace_activities"]),
            ]
        )
    )
    rag_index = build_index(knowledge_chunks)
    save_index(rag_index, project_name)

    return course