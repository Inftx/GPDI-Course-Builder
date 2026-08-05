from datetime import datetime
from pathlib import Path

import streamlit as st

from modules.session_manager import get_current_project
from services.export.export_manager import export_document
from services.output.output_manager import list_outputs, load_output


OUTPUT_TYPES = {
    "Lesson Plans": "lesson_plans",
    "Facilitator Guides": "facilitator_guides",
    "Assessments": "assessments",
    "Quizzes": "quizzes",
    "Teaching Scripts": "teaching_scripts",
    "Student Notes": "student_notes",
    "PowerPoints": "powerpoints",
}


def main() -> None:
    st.set_page_config(
        page_title="AI Output Library",
        page_icon="📂",
    )

    st.title("📂 AI Output Library")

    project = get_current_project()

    if not project:
        st.warning("Please select a project first.")
        st.stop()

    output_label = st.selectbox(
        "Output Type",
        list(OUTPUT_TYPES),
    )
    output_type = OUTPUT_TYPES[output_label]
    output_files = list_outputs(
        project,
        output_type,
    )

    if not output_files:
        st.info("No saved outputs are available for this category.")
        st.stop()

    selected_file = st.selectbox(
        "Saved Outputs",
        output_files,
        format_func=lambda file_path: file_path.name,
    )
    content = load_output(selected_file)
    created_at = datetime.fromtimestamp(
        selected_file.stat().st_ctime
    ).strftime("%Y-%m-%d %H:%M:%S")

    st.subheader(selected_file.name)
    st.write(f"Creation Date: {created_at}")
    st.code(
        content,
        language="markdown",
    )

    copy_column, regenerate_column, export_column = st.columns(3)

    with copy_column:
        if st.button("📋 Copy Content", use_container_width=True):
            st.toast(
                "Use the copy control in the Markdown content above."
            )

    with regenerate_column:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.switch_page("pages/4_🤖_AI_Workspace.py")

    with export_column:
        include_logo = st.checkbox(
            "Include GPDI Logo",
            value=False,
            help="Insert the logo at the top of the exported DOCX when available.",
        )

        if st.button("📄 Export DOCX", use_container_width=True):
            try:
                exports_folder = Path("projects") / project / "exports"
                exports_folder.mkdir(parents=True, exist_ok=True)

                output_filename = selected_file.stem + ".docx"
                output_path = exports_folder / output_filename

                export_document(
                    content,
                    "docx",
                    output_path,
                    title=selected_file.stem,
                    include_logo=include_logo,
                )

                st.success("✅ Document exported successfully")
                st.write("Saved path:")
                st.code(str(output_path))

            except Exception as error:
                st.error(error)


if __name__ == "__main__":
    main()
