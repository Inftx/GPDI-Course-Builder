import json
from pathlib import Path

import streamlit as st

from modules.session_manager import get_current_project
from services.ai.provider_manager import ProviderManager
from services.generators.assessment_generator import generate_assessment
from services.generators.facilitator_guide_generator import (
    generate_facilitator_guide,
)
from services.generators.lesson_plan_generator import generate_lesson_plan
from services.generators.teaching_script_generator import generate_teaching_script
from services.generators.training_pack_generator import generate_training_pack
from services.jobs.job_manager import (
    complete_job,
    create_job,
    fail_job,
    start_job,
)
from services.output.output_manager import save_output
from services.workflows import GenerationWizard

WIZARD_SESSION_KEY = "generation_wizard"
GENERATION_RUN_KEY = "ai_workspace_generation_run"
GENERATION_COMPLETE_KEY = "ai_workspace_generation_complete"
GENERATION_RESULT_KEY = "ai_workspace_generation_result"
GENERATION_ERROR_KEY = "ai_workspace_generation_error"
GENERATION_TRAINING_PACK_KEY = "ai_workspace_training_pack"

WIZARD_OUTPUT_TYPES = [
    "Lesson Plan",
    "Facilitator Guide",
    "Teaching Script",
    "Assessment",
    "Training Pack",
]

OUTPUT_TYPE_TO_TASK = {
    "Training Pack": "Complete Training Pack",
}

OUTPUT_TYPE_TO_SAVE_FOLDER = {
    "Lesson Plan": "lesson_plans",
    "Facilitator Guide": "facilitator_guides",
    "Assessment": "assessments",
    "Teaching Script": "teaching_scripts",
}


def _get_wizard() -> GenerationWizard:
    if WIZARD_SESSION_KEY not in st.session_state:
        st.session_state[WIZARD_SESSION_KEY] = GenerationWizard()
    return st.session_state[WIZARD_SESSION_KEY]


def _reset_wizard() -> None:
    st.session_state[WIZARD_SESSION_KEY] = GenerationWizard()
    for key in [
        GENERATION_RUN_KEY,
        GENERATION_COMPLETE_KEY,
        GENERATION_RESULT_KEY,
        GENERATION_ERROR_KEY,
        GENERATION_TRAINING_PACK_KEY,
    ]:
        st.session_state.pop(key, None)


def _get_available_projects() -> list[str]:
    projects_folder = Path("projects")
    if not projects_folder.exists():
        return []
    return sorted(
        [
            folder.name
            for folder in projects_folder.iterdir()
            if folder.is_dir()
        ]
    )


def _run_project_job(project_name: str, task_type: str, execute_callable):
    job = create_job(project_name, task_type)
    start_job(project_name, job["job_id"])

    try:
        result = execute_callable()
        complete_job(project_name, job["job_id"])
        return result

    except Exception as error:
        fail_job(project_name, job["job_id"], str(error))
        raise


def main() -> None:
    st.set_page_config(
        page_title="AI Workspace",
        page_icon="🤖",
    )

    st.title("🤖 AI Workspace")

    wizard = _get_wizard()
    wizard_state = wizard.get_state()

    current_project = get_current_project()
    if not wizard_state.project and current_project:
        wizard.set_project(current_project)
        wizard_state = wizard.get_state()

    project = wizard_state.project
    selected_project = project

    available_projects = _get_available_projects()

    st.subheader(f"Step {wizard_state.step} of 6: {wizard.current_step()}")
    st.progress(wizard_state.step / 6)

    if st.button("Reset Wizard", type="secondary"):
        _reset_wizard()
        st.rerun()

    if wizard_state.step == 1:
        if not available_projects:
            st.warning("No projects exist. Create a project first.")
            st.stop()

        selected_index = 0
        if selected_project in available_projects:
            selected_index = available_projects.index(selected_project)

        project_choice = st.selectbox(
            "Select Project",
            available_projects,
            index=selected_index,
        )

        if st.button("Next ➜", use_container_width=True):
            if not project_choice:
                st.warning("Please select a project before continuing.")
            else:
                wizard.set_project(project_choice)
                wizard.next_step()
                st.rerun()

        st.stop()

    if not project:
        st.warning("Please select a project first.")
        st.stop()

    course_file = Path("projects") / project / "course.json"
    if not course_file.exists():
        st.warning("Please build the Course Knowledge Base first.")
        st.stop()

    provider = ProviderManager.get_provider("ollama")
    output_type = wizard_state.output_type

    if wizard_state.step == 2:
        module_name = st.text_input(
            "Module Name",
            value=wizard_state.module or "",
        )

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("Next ➜", use_container_width=True):
                if not module_name.strip():
                    st.warning("Please enter a module name before continuing.")
                else:
                    wizard.set_module(module_name.strip())
                    wizard.next_step()
                    st.rerun()

        st.stop()

    if wizard_state.step == 3:
        output_type_choice = st.selectbox(
            "Select Output Type",
            WIZARD_OUTPUT_TYPES,
            index=WIZARD_OUTPUT_TYPES.index(output_type)
            if output_type in WIZARD_OUTPUT_TYPES
            else 0,
        )

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("Next ➜", use_container_width=True):
                wizard.set_output_type(output_type_choice)
                wizard.next_step()
                st.rerun()

        st.stop()

    if wizard_state.step == 4:
        instructions = st.text_area(
            "Additional Instructions",
            value=wizard_state.options.get("instructions", ""),
            height=180,
            placeholder="Example: Create a 3-hour lesson with activities and formative assessments.",
        )

        audience = st.selectbox(
            "Audience",
            ["General learners", "Entry-level learners", "Experienced professionals"],
            index=["General learners", "Entry-level learners", "Experienced professionals"].index(
                wizard_state.options.get("audience", "General learners")
            ),
        )

        teaching_style = st.selectbox(
            "Teaching Style",
            ["Interactive", "Lecture-based", "Practical"],
            index=["Interactive", "Lecture-based", "Practical"].index(
                wizard_state.options.get("teaching_style", "Interactive")
            ),
        )

        detail_level = st.selectbox(
            "Detail Level",
            ["Basic", "Moderate", "Detailed"],
            index=["Basic", "Moderate", "Detailed"].index(
                wizard_state.options.get("detail_level", "Basic")
            ),
        )

        if output_type == "Lesson Plan":
            duration_hours = st.number_input(
                "Duration (hours)",
                min_value=0.5,
                step=0.5,
                value=wizard_state.options.get("duration_hours", 0.5),
            )

        elif output_type == "Facilitator Guide":
            duration_hours = st.number_input(
                "Session Duration (hours)",
                min_value=0.5,
                step=0.5,
                value=wizard_state.options.get("duration_hours", 0.5),
            )

        elif output_type == "Assessment":
            number_of_questions = st.number_input(
                "Number of Questions",
                min_value=1,
                value=wizard_state.options.get("number_of_questions", 10),
                step=1,
            )

            difficulty = st.selectbox(
                "Difficulty",
                ["Easy", "Moderate", "Advanced"],
                index=["Easy", "Moderate", "Advanced"].index(
                    wizard_state.options.get("difficulty", "Moderate")
                ),
            )

        elif output_type == "Teaching Script":
            duration_hours = st.number_input(
                "Session Duration",
                min_value=0.5,
                step=0.5,
                value=wizard_state.options.get("duration_hours", 0.5),
            )

        elif output_type == "Training Pack":
            duration_hours = st.number_input(
                "Session Duration (hours)",
                min_value=0.5,
                step=0.5,
                value=wizard_state.options.get("duration_hours", 0.5),
            )

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("Next ➜", use_container_width=True):
                options = {
                    "instructions": instructions,
                    "audience": audience,
                    "teaching_style": teaching_style,
                    "detail_level": detail_level,
                }

                if output_type in ["Lesson Plan", "Facilitator Guide", "Teaching Script", "Training Pack"]:
                    options["duration_hours"] = duration_hours

                if output_type == "Assessment":
                    options["number_of_questions"] = number_of_questions
                    options["difficulty"] = difficulty

                wizard.set_options(options)
                wizard.next_step()
                st.rerun()

        st.stop()

    if wizard_state.step == 5:
        st.write("**Review your configuration before generating.**")
        st.write(f"**Project:** {project}")
        st.write(f"**Module:** {wizard_state.module}")
        st.write(f"**Output Type:** {output_type}")
        st.write("**Options:**")

        for key, value in wizard_state.options.items():
            st.write(f"- {key}: {value}")

        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("✅ Generate", use_container_width=True):
                wizard.next_step()
                st.session_state[GENERATION_RUN_KEY] = True
                st.rerun()

        st.stop()

    if wizard_state.step == 6:
        if st.session_state.get(GENERATION_RUN_KEY) and not st.session_state.get(GENERATION_COMPLETE_KEY):
            try:
                if output_type == "Lesson Plan":
                    result = _run_project_job(
                        project,
                        "Lesson Plan",
                        lambda: generate_lesson_plan(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                            audience=wizard_state.options["audience"],
                            teaching_style=wizard_state.options["teaching_style"],
                            detail_level=wizard_state.options["detail_level"],
                        ),
                    )
                    st.success("Lesson plan generated and saved successfully.")
                    st.subheader("Lesson Plan")
                    st.markdown(result)

                elif output_type == "Facilitator Guide":
                    result = _run_project_job(
                        project,
                        "Facilitator Guide",
                        lambda: generate_facilitator_guide(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                        ),
                    )
                    st.success("Facilitator guide generated and saved successfully.")
                    st.subheader("Facilitator Guide")
                    st.markdown(result)

                elif output_type == "Assessment":
                    result = _run_project_job(
                        project,
                        "Assessment",
                        lambda: generate_assessment(
                            project,
                            wizard_state.module,
                            wizard_state.options["number_of_questions"],
                            wizard_state.options["difficulty"],
                            provider,
                            audience=wizard_state.options["audience"],
                            teaching_style=wizard_state.options["teaching_style"],
                            detail_level=wizard_state.options["detail_level"],
                        ),
                    )
                    st.success("Assessment generated and saved successfully.")
                    st.subheader("Assessment")
                    st.markdown(result)

                elif output_type == "Teaching Script":
                    result = _run_project_job(
                        project,
                        "Teaching Script",
                        lambda: generate_teaching_script(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                            audience=wizard_state.options["audience"],
                            teaching_style=wizard_state.options["teaching_style"],
                            detail_level=wizard_state.options["detail_level"],
                        ),
                    )
                    st.success("Teaching script generated and saved successfully.")
                    st.subheader("Teaching Script")
                    st.markdown(result)

                elif output_type == "Training Pack":
                    training_pack = _run_project_job(
                        project,
                        "Complete Training Pack",
                        lambda: generate_training_pack(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                        ),
                    )
                    progress_stages = [
                        ("Lesson Plan", "lesson_plan"),
                        ("Facilitator Guide", "facilitator_guide"),
                        ("Teaching Script", "teaching_script"),
                        ("Assessment", "assessment"),
                    ]

                    for progress, (label, _) in enumerate(progress_stages, start=1):
                        st.progress(progress * 25, text=f"{label} generated.")

                    st.success("✅ Training Pack Generated Successfully")

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

                st.session_state[GENERATION_RESULT_KEY] = True
                st.session_state[GENERATION_COMPLETE_KEY] = True
                st.session_state[GENERATION_RUN_KEY] = False

            except Exception as error:
                st.session_state[GENERATION_ERROR_KEY] = str(error)
                st.error(error)

        elif st.session_state.get(GENERATION_COMPLETE_KEY):
            st.success("Generation completed.")

        else:
            st.info("Click Generate on the Review step to start generation.")

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("Reset Wizard", use_container_width=True):
                _reset_wizard()
                st.rerun()

        if st.session_state.get(GENERATION_ERROR_KEY):
            st.error(st.session_state[GENERATION_ERROR_KEY])

        st.stop()


if __name__ == "__main__":
    main()
