import streamlit as st

from modules.session_manager import get_current_project
from modules.course_builder import build_course


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Course Builder",
    page_icon="🧠"
)

st.title("🧠 Course Builder")

project = get_current_project()

if not project:

    st.warning(
        "Please select a project in the Project Manager first."
    )

    st.stop()

st.success(f"Current Project: {project}")

st.divider()

st.write("""
This tool combines all uploaded educational documents
into a single Course Knowledge Base.

Once built, every future AI feature will use this
Course Knowledge instead of reading documents directly.
""")

st.divider()

if st.button(
    "Build Course Knowledge Base",
    use_container_width=True
):

    with st.spinner(
        "Building course..."
    ):

        course = build_course(project)

    st.success(
        "Course knowledge successfully built."
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Documents",
            len(course["documents"])
        )

    with col2:

        st.metric(
            "Modules",
            len(course.get("modules") or [])
        )

    with col3:

        st.metric(
            "Learning Outcomes",
            len(course["learning_outcomes"])
        )

    st.divider()

    st.subheader("Documents")

    if course["documents"]:

        for document in course["documents"]:

            st.write(f"• {document}")

    else:

        st.info("No uploaded documents found.")

    st.divider()

    st.subheader("Course Knowledge")

    st.json(course)