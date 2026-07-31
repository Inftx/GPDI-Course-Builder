import json
from pathlib import Path

import streamlit as st

from modules.session_manager import get_current_project
from modules.ai_engine import AILecturer
from services.ai.provider_manager import ProviderManager
from services.rag.chunker import chunk_document
from services.rag.indexer import build_index
from services.rag.retriever import retrieve_context
from services.output.output_manager import save_output
from services.generators.lesson_plan_generator import generate_lesson_plan
from services.generators.facilitator_guide_generator import (
    generate_facilitator_guide,
)
from services.generators.assessment_generator import generate_assessment
from services.generators.teaching_script_generator import generate_teaching_script
from services.generators.training_pack_generator import generate_training_pack


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

        "Quiz",

        "Complete Training Pack"

    ]

)

output_types = {
    "Lesson Plan": "lesson_plans",
    "Facilitator Guide": "facilitator_guides",
    "Assessment": "assessments",
    "Quiz": "quizzes",
    "Teaching Script": "teaching_scripts",
    "Student Notes": "student_notes",
    "PowerPoint": "powerpoints",
}

instructions = st.text_area(

    "Additional Instructions",

    height=180,

    placeholder="Example: Create a 3-hour lesson with activities and formative assessments."

)

if task == "Lesson Plan":

    module_name = st.text_input(
        "Module Name"
    )

    duration_hours = st.number_input(
        "Duration (hours)",
        min_value=0.5,
        step=0.5,
    )

    generate_label = "Generate Lesson Plan"

elif task == "Facilitator Guide":

    module_name = st.text_input(
        "Module Name"
    )

    duration_hours = st.number_input(
        "Session Duration (hours)",
        min_value=0.5,
        step=0.5,
    )

    generate_label = "Generate Facilitator Guide"

elif task == "Assessment":

    module_name = st.text_input(
        "Module Name"
    )

    number_of_questions = st.number_input(
        "Number of Questions",
        min_value=1,
        value=10,
        step=1,
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Moderate", "Advanced"],
    )

    generate_label = "Generate Assessment"

elif task == "Teaching Script":

    module_name = st.text_input(
        "Module Name"
    )

    duration_hours = st.number_input(
        "Session Duration",
        min_value=0.5,
        step=0.5,
    )

    generate_label = "Generate Teaching Script"

elif task == "Complete Training Pack":

    module_name = st.text_input(
        "Module Name"
    )

    duration_hours = st.number_input(
        "Session Duration (hours)",
        min_value=0.5,
        step=0.5,
    )

    generate_label = "🚀 Generate Complete Training Pack"

else:

    generate_label = "🚀 Generate"

if st.button(

    generate_label,

    use_container_width=True

):

    if task == "Lesson Plan":

        with st.spinner(
            "Ollama is generating your lesson plan..."
        ):

            try:

                result = generate_lesson_plan(
                    project,
                    module_name,
                    duration_hours,
                    provider,
                )

                st.success(
                    "Lesson plan generated and saved successfully."
                )

                st.divider()

                st.subheader(
                    "Lesson Plan"
                )

                st.markdown(result)

            except Exception as error:

                st.error(error)

        st.stop()

    if task == "Facilitator Guide":

        with st.spinner(
            "Ollama is generating your facilitator guide..."
        ):

            try:

                result = generate_facilitator_guide(
                    project,
                    module_name,
                    duration_hours,
                    provider,
                )

                st.success(
                    "Facilitator guide generated and saved successfully."
                )

                st.divider()

                st.subheader(
                    "Facilitator Guide"
                )

                st.markdown(result)

            except Exception as error:

                st.error(error)

        st.stop()

    if task == "Assessment":

        with st.spinner(
            "Ollama is generating your assessment..."
        ):

            try:

                result = generate_assessment(
                    project,
                    module_name,
                    number_of_questions,
                    difficulty,
                    provider,
                )

                st.success(
                    "Assessment generated and saved successfully."
                )

                st.divider()

                st.subheader(
                    "Assessment"
                )

                st.markdown(result)

            except Exception as error:

                st.error(error)

        st.stop()

    if task == "Teaching Script":

        with st.spinner(
            "Ollama is generating your teaching script..."
        ):

            try:

                result = generate_teaching_script(
                    project,
                    module_name,
                    duration_hours,
                    provider,
                )

                st.success(
                    "Teaching script generated and saved successfully."
                )

                st.divider()

                st.subheader(
                    "Teaching Script"
                )

                st.markdown(result)

            except Exception as error:

                st.error(error)

        st.stop()

    if task == "Complete Training Pack":

        progress_bar = st.progress(
            0,
            text="Generating Lesson Plan...",
        )

        with st.spinner(
            "Ollama is generating your complete training pack..."
        ):

            try:

                training_pack = generate_training_pack(
                    project,
                    module_name,
                    duration_hours,
                    provider,
                )

                progress_stages = [
                    ("Lesson Plan", "lesson_plan"),
                    ("Facilitator Guide", "facilitator_guide"),
                    ("Teaching Script", "teaching_script"),
                    ("Assessment", "assessment"),
                ]

                for progress, (label, _) in enumerate(
                    progress_stages,
                    start=1,
                ):
                    progress_bar.progress(
                        progress * 25,
                        text=f"{label} generated.",
                    )

                st.success(
                    "✅ Training Pack Generated Successfully"
                )

                lesson_tab, guide_tab, script_tab, assessment_tab = st.tabs(
                    [
                        "📘 Lesson Plan",
                        "👨‍🏫 Facilitator Guide",
                        "🎤 Teaching Script",
                        "📝 Assessment",
                    ]
                )

                with lesson_tab:
                    st.markdown(training_pack["lesson_plan"])

                with guide_tab:
                    st.markdown(training_pack["facilitator_guide"])

                with script_tab:
                    st.markdown(training_pack["teaching_script"])

                with assessment_tab:
                    st.markdown(training_pack["assessment"])

            except Exception as error:

                st.error(error)

        st.stop()

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

            saved_path = save_output(
                project,
                output_types[task],
                result,
            )

            st.success(
                "Generation completed."
            )

            st.success(
                "✅ Output saved successfully."
            )

            st.write(
                "Saved Location:"
            )

            st.code(
                str(saved_path)
            )

            st.divider()

            st.subheader(
                f"{task}"
            )

            st.markdown(result)

        except Exception as error:

            st.error(error)
