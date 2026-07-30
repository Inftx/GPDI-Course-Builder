import json
from pathlib import Path

import streamlit as st

from modules.session_manager import get_current_project
from modules.ai_engine import AILecturer
from modules.ollama_provider import OllamaProvider


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

provider = OllamaProvider()

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

    with st.spinner(

        "Ollama is generating your content..."

    ):

        prompt = engine.generate_prompt(

            f"""

Create a professional {task}.

Use the uploaded qualification information.

Additional Instructions:

{instructions}

Return the content in a professional educational format.

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