import streamlit as st

from modules.project_manager import (
    create_project,
    get_projects
)

from modules.session_manager import (
    set_current_project,
    get_current_project
)

from modules.file_manager import (
    save_uploaded_file,
    save_extracted_text
)

from modules.document_processor import process_document
from modules.document_analyzer import analyze_document
from modules.metadata_manager import save_document_metadata


st.title("📁 Project Manager")


# ----------------------------
# CREATE PROJECT
# ----------------------------

st.subheader("Create New Project")

project_name = st.text_input(
    "Project Name",
    placeholder="Example: Business & Office Administration"
)

if st.button("Create Project"):

    if not project_name.strip():

        st.warning(
            "Please enter a project name."
        )

    else:

        success, message = create_project(
            project_name
        )

        if success:

            st.success(message)

            set_current_project(
                project_name
            )

            st.rerun()

        else:

            st.error(message)


st.divider()


# ----------------------------
# OPEN PROJECT
# ----------------------------

st.subheader("Existing Projects")

projects = get_projects()

if projects:

    selected_project = st.selectbox(
        "Select Current Project",
        projects
    )

    if st.button("Open Project"):

        set_current_project(
            selected_project
        )

        st.success(
            f"Opened: {selected_project}"
        )

else:

    st.info(
        "No projects available."
    )


st.divider()


# ----------------------------
# CURRENT PROJECT
# ----------------------------

current_project = get_current_project()

if current_project:

    st.success(
        f"Current Project: {current_project}"
    )

else:

    st.warning(
        "No project selected."
    )


st.divider()


# ----------------------------
# DOCUMENT UPLOAD
# ----------------------------

st.subheader("Upload Project Documents")

if current_project:

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=[
            "pdf",
            "docx",
            "txt",
            "png",
            "jpg",
            "jpeg"
        ]
    )

    if uploaded_file:

        if st.button("Save Document"):

            try:

                # Process document
                extracted_text = process_document(
                    uploaded_file
                )

                # Analyze document
                analysis = analyze_document(
                    extracted_text
                )

                # Save original file
                file_path = save_uploaded_file(
                    uploaded_file,
                    current_project
                )

                # Save extracted text
                text_path = save_extracted_text(
                    extracted_text,
                    uploaded_file.name,
                    current_project
                )

                # Save metadata
                metadata_path = save_document_metadata(
                    current_project,
                    uploaded_file.name,
                    analysis
                )

                st.success(
                    f"Original saved: {file_path.name}"
                )

                st.success(
                    f"Extracted text saved: {text_path.name}"
                )

                st.success(
                    f"Metadata saved: {metadata_path.name}"
                )

                st.subheader("Extracted Text")

                st.text_area(
                    "Document Contents",
                    extracted_text,
                    height=400,
                    key="document_contents"
                )

                st.divider()

                st.subheader("📊 Document Analysis")

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Word Count",
                        analysis["word_count"]
                    )

                    st.metric(
                        "Characters",
                        analysis["character_count"]
                    )

                with col2:

                    st.metric(
                        "Estimated Pages",
                        analysis["estimated_pages"]
                    )

                    st.metric(
                        "Reading Time",
                        f"{analysis['reading_time']} min"
                    )

                st.subheader("Detected Headings")

                if analysis["headings"]:

                    for heading in analysis["headings"]:

                        st.write(f"✅ {heading}")

                else:

                    st.info(
                        "No known headings detected."
                    )

                st.subheader("Top Keywords")

                for word, count in analysis["keywords"]:

                    st.write(
                        f"• {word} ({count})"
                    )

            except Exception as error:

                st.error(
                    str(error)
                )

else:

    st.warning(
        "Please create or open a project first."
    )