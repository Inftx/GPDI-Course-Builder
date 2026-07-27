import streamlit as st

from modules.session_manager import get_current_project

from modules.file_manager import (
    save_uploaded_file,
    save_extracted_text
)

from modules.document_processor import process_document

from modules.document_analyzer import analyze_document

from modules.metadata_manager import save_document_metadata


st.title("📄 Upload Documents")

st.write(
    "Upload learner guides, facilitator guides, workbooks and other supporting documents."
)

st.divider()

# ------------------------------------------
# ACTIVE PROJECT
# ------------------------------------------

project = get_current_project()

if not project:

    st.warning(
        "Please select a project first using the Project Manager page."
    )

    st.stop()

st.success(f"Current Project: {project}")

st.divider()

# ------------------------------------------
# FILE UPLOADER
# ------------------------------------------

uploaded_file = st.file_uploader(

    "Choose a document",

    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]

)

if uploaded_file:

    with st.spinner("Processing document..."):

        # Save original file

        save_uploaded_file(
            uploaded_file,
            project
        )

        # Extract text

        extracted_text = process_document(
            uploaded_file
        )

        # Save extracted text

        save_extracted_text(

            extracted_text,

            uploaded_file.name,

            project

        )

        # Analyse document

        analysis = analyze_document(
            extracted_text
        )

        # Save metadata

        save_document_metadata(

            project,

            uploaded_file.name,

            analysis

        )

    st.success("Document processed successfully!")

    st.divider()

    st.subheader("Document Statistics")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Words",
            analysis["word_count"]
        )

        st.metric(
            "Pages (Estimated)",
            analysis["estimated_pages"]
        )

    with col2:

        st.metric(
            "Characters",
            analysis["character_count"]
        )

        st.metric(
            "Reading Time",
            f'{analysis["reading_time"]} min'
        )

    st.divider()

    st.subheader("Detected Headings")

    if analysis["headings"]:

        for heading in analysis["headings"]:

            st.write("•", heading)

    else:

        st.info("No headings detected.")

    st.divider()

    st.subheader("Top Keywords")

    for word, count in analysis["keywords"]:

        st.write(f"**{word}** ({count})")

    st.divider()

    st.subheader("Extracted Text")

    st.text_area(
    "Extracted Document Text",
    extracted_text,
    height=350
)