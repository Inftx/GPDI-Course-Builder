import json
from pathlib import Path

import streamlit as st

from modules.session_manager import get_current_project
from modules.ai_engine import AILecturer
from services.ai.provider_manager import ProviderManager
from services.rag.chunker import chunk_document
from services.rag.indexer import build_index
from services.rag.retriever import retrieve_context


st.set_page_config(
    page_title="AI Workspace",
    page_icon="🤖"
)

st.title("🤖 AI Workspace")

project = get_current_project()

if not project:

    st.warning(
        "Please select a project first."
    )

    st.stop()

course_file = (
    Path("projects")
    / project
    / "course.json"
)

if not course_file.exists():

    st.warning(
        "Please build the Course Knowledge Base first."
    )

    st.stop()

with open(
    course_file,
    "r",
    encoding="utf-8"
) as file:

    course = json.load(file)

engine = AILecturer(course)

provider = ProviderManager.get_provider("ollama")

task = st.selectbox(

    "Select AI Task",

    [

        "Lesson Plan",

        "Assessment",

        "Facilitator Guide",

        "PowerPoint",

        "Teaching Script",

        "Student Notes",

        "Quiz"

    ]

)

instructions = st.text_area(

    "Additional Instructions",

    height=180,

    placeholder="Example: Create a 3-hour lesson with activities and formative assessments."

)

if st.button(

    "🚀 Generate",

    use_container_width=True

):

    course_text = "\n\n".join(
        [
            "Course Documents\n" + "\n".join(course["documents"]),
            "\n".join(course["modules"]),
            "Learning Outcomes\n" + "\n".join(course["learning_outcomes"]),
            "Assessment Criteria\n" + "\n".join(course["assessment_criteria"]),
            "Knowledge Requirements\n" + "\n".join(
                course["knowledge_requirements"]
            ),
            "Practical Activities\n" + "\n".join(
                course["practical_activities"]
            ),
            "Workplace Activities\n" + "\n".join(
                course["workplace_activities"]
            ),
        ]
    )

    user_request = f"""

Create a professional {task}.

Use the uploaded qualification information.

Additional Instructions:

{instructions}

Return the content in a professional educational format.

"""

    chunks = chunk_document(course_text)
    index = build_index(chunks)
    retrieved_context = retrieve_context(
        index,
        f"{task} {instructions}",
    )

    with st.spinner(

        "Ollama is generating your content..."

    ):

        prompt = engine.generate_prompt(

            f"""

Course Context

{retrieved_context}

User Request

{user_request}

"""

        )

        try:

            result = provider.generate(
                prompt
            )

            st.success(
                "Generation completed."
            )

            st.divider()

            st.subheader(
                f"{task}"
            )

            st.markdown(result)

        except Exception as error:

            st.error(error)
