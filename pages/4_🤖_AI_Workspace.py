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
from services.knowledge.course_selection import (
    get_course_module_options,
    resolve_module_identifier,
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


def _render_generated_output(
    output_type: str,
    result: str | dict[str, str],
) -> None:
    if isinstance(result, str):
        st.subheader(output_type)
        st.markdown(result)
        return

    lesson_tab, guide_tab, script_tab, assessment_tab = st.tabs(
        [
            "📘 Lesson Plan",
            "👨‍🏫 Facilitator Guide",
            "🎤 Teaching Script",
            "📝 Assessment",
        ]
    )

    with lesson_tab:
        st.markdown(result["lesson_plan"])

    with guide_tab:
        st.markdown(result["facilitator_guide"])

    with script_tab:
        st.markdown(result["teaching_script"])

    with assessment_tab:
        st.markdown(result["assessment"])


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
        st.warning("Please build the Course Knowledge Base before generating content.")
        st.stop()

    try:
        course_data = json.loads(course_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        st.error(f"Could not read the Course Knowledge Base: {error}")
        st.stop()
    if not isinstance(course_data, dict):
        st.error("The Course Knowledge Base must contain a JSON object.")
        st.stop()

    module_options = get_course_module_options(course_data)
    if not module_options:
        st.warning(
            "No processed modules are available. Build the Course Knowledge "
            "Base after processing project documents, then try again."
        )
        st.stop()

    output_type = wizard_state.output_type

    if wizard_state.step == 2:
        module_by_id = {
            option.identifier: option for option in module_options
        }
        module_ids = [option.identifier for option in module_options]
        selected_module_id = resolve_module_identifier(
            module_options,
            wizard_state.module,
        ) or module_ids[0]
        selected_module_id = st.selectbox(
            "Select Module",
            options=module_ids,
            index=module_ids.index(selected_module_id),
            format_func=lambda identifier: module_by_id[identifier].label,
            key=f"ai_workspace_module_{project}_{hash(tuple(module_ids))}",
        )
        selected_module = module_by_id[selected_module_id]

        if selected_module.topics:
            topic_by_id = {
                topic.identifier: topic for topic in selected_module.topics
            }
            topic_ids = [topic.identifier for topic in selected_module.topics]
            selected_topic_id = (
                wizard_state.knowledge_topic
                if (
                    wizard_state.module == selected_module_id
                    and wizard_state.knowledge_topic in topic_by_id
                )
                else topic_ids[0]
            )
            selected_topic_id = st.selectbox(
                "Select Knowledge Topic",
                options=topic_ids,
                index=topic_ids.index(selected_topic_id),
                format_func=lambda identifier: topic_by_id[identifier].label,
                key=(
                    f"ai_workspace_topic_{project}_{selected_module_id}_"
                    f"{hash(tuple(topic_ids))}"
                ),
            )
        else:
            selected_topic_id = None
            st.info(
                "No processed knowledge topics are available for this module. "
                "Choose another module or rebuild the Course Knowledge Base."
            )

        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("⬅ Back", use_container_width=True):
                wizard.previous_step()
                st.rerun()

        with cols[1]:
            if st.button("Next ➜", use_container_width=True):
                if not selected_topic_id:
                    st.warning(
                        "This module has no selectable processed knowledge "
                        "topics. Choose another module or rebuild the Course "
                        "Knowledge Base."
                    )
                else:
                    wizard.set_module(
                        selected_module.identifier,
                        selected_module.label,
                    )
                    selected_topic = topic_by_id[selected_topic_id]
                    wizard.set_knowledge_topic(
                        selected_topic.identifier,
                        selected_topic.label,
                    )
                    wizard.next_step()
                    st.rerun()

        st.stop()

    provider = ProviderManager.get_provider("ollama")

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

        elif output_type == "Training Pack":
            duration_hours = st.number_input(
                "Session Duration (hours)",
                min_value=0.5,
                step=0.5,
                value=wizard_state.options.get("duration_hours", 0.5),
            )

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

                if output_type in ["Assessment", "Training Pack"]:
                    options["number_of_questions"] = number_of_questions
                    options["difficulty"] = difficulty

                wizard.set_options(options)
                wizard.next_step()
                st.rerun()

        st.stop()

    if wizard_state.step == 5:
        st.write("**Review your configuration before generating.**")
        st.write(f"**Project:** {project}")
        st.write(f"**Module:** {wizard_state.module_label or wizard_state.module}")
        st.write(
            f"**Knowledge Topic:** "
            f"{wizard_state.knowledge_topic_label or wizard_state.knowledge_topic}"
        )
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
                result: str | dict[str, str] | None = None

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
                            knowledge_topic_id=wizard_state.knowledge_topic,
                        ),
                    )
                    st.success("Lesson plan generated and saved successfully.")
                    _render_generated_output(output_type, result)

                elif output_type == "Facilitator Guide":
                    result = _run_project_job(
                        project,
                        "Facilitator Guide",
                        lambda: generate_facilitator_guide(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                            audience=wizard_state.options["audience"],
                            teaching_style=wizard_state.options["teaching_style"],
                            detail_level=wizard_state.options["detail_level"],
                            knowledge_topic_id=wizard_state.knowledge_topic,
                        ),
                    )
                    st.success("Facilitator guide generated and saved successfully.")
                    _render_generated_output(output_type, result)

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
                            knowledge_topic_id=wizard_state.knowledge_topic,
                        ),
                    )
                    st.success("Assessment generated and saved successfully.")
                    _render_generated_output(output_type, result)

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
                            knowledge_topic_id=wizard_state.knowledge_topic,
                        ),
                    )
                    st.success("Teaching script generated and saved successfully.")
                    _render_generated_output(output_type, result)

                elif output_type == "Training Pack":
                    training_pack = _run_project_job(
                        project,
                        "Complete Training Pack",
                        lambda: generate_training_pack(
                            project,
                            wizard_state.module,
                            wizard_state.options["duration_hours"],
                            provider,
                            audience=wizard_state.options["audience"],
                            teaching_style=wizard_state.options["teaching_style"],
                            detail_level=wizard_state.options["detail_level"],
                            knowledge_topic_id=wizard_state.knowledge_topic,
                            number_of_questions=wizard_state.options[
                                "number_of_questions"
                            ],
                            difficulty=wizard_state.options["difficulty"],
                        ),
                    )
                    result = training_pack
                    progress_stages = [
                        ("Lesson Plan", "lesson_plan"),
                        ("Facilitator Guide", "facilitator_guide"),
                        ("Teaching Script", "teaching_script"),
                        ("Assessment", "assessment"),
                    ]

                    for progress, (label, _) in enumerate(progress_stages, start=1):
                        st.progress(progress * 25, text=f"{label} generated.")

                    st.success("✅ Training Pack Generated Successfully")
                    _render_generated_output(output_type, training_pack)

                if result is None:
                    raise RuntimeError(
                        f"Generation returned no content for '{output_type}'."
                    )

                st.session_state[GENERATION_RESULT_KEY] = result
                st.session_state[GENERATION_COMPLETE_KEY] = True
                st.session_state[GENERATION_RUN_KEY] = False

            except Exception as error:
                st.session_state[GENERATION_ERROR_KEY] = str(error)
                st.error(error)

        elif st.session_state.get(GENERATION_COMPLETE_KEY):
            st.success("Generation completed.")
            generation_result = st.session_state.get(GENERATION_RESULT_KEY)
            if isinstance(generation_result, (str, dict)):
                _render_generated_output(output_type, generation_result)
            else:
                st.warning(
                    "The generated content is no longer available in this "
                    "session. Generate it again to display the result."
                )

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
