import streamlit as st

from modules.session_manager import get_current_project

from modules.file_manager import (
    save_uploaded_file,
    save_extracted_text,
    save_formatted_text
)

from modules.document_processor import process_document
from modules.document_analyzer import analyze_document
from modules.metadata_manager import save_document_metadata


st.set_page_config(page_title="Upload Documents", page_icon="📄")

st.title("📄 Upload Documents")

project = get_current_project()

if not project:
    st.warning("Please select a project in the Project Manager first.")
    st.stop()

st.success(f"Current Project: {project}")

uploaded_file = st.file_uploader(
    "Upload a document",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
)

if uploaded_file:

    with st.spinner("Processing document..."):

        # Save original file
        save_uploaded_file(
            uploaded_file,
            project
        )

        # Process document
        result = process_document(uploaded_file)

        raw_text = result["raw"]
        cleaned_text = result["clean"]
        structured_text = result["structured"]

        # Save cleaned text
        save_extracted_text(
            cleaned_text,
            uploaded_file.name,
            project
        )

        # Save structured text
        save_formatted_text(
            structured_text,
            uploaded_file.name,
            project
        )

        # Analyse structured text
        analysis = analyze_document(structured_text)

        # Save metadata
        save_document_metadata(
            project,
            uploaded_file.name,
            analysis
        )

    st.success("✅ Document processed successfully.")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Words",
        analysis["word_count"]
    )

    col2.metric(
        "Characters",
        analysis["character_count"]
    )

    col3.metric(
        "Pages",
        analysis["estimated_pages"]
    )

    col4.metric(
        "Reading Time",
        f"{analysis['reading_time']} min"
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        [
            "📄 Raw Text",
            "🧹 Cleaned Text",
            "🧠 Structured Document"
        ]
    )

    with tab1:

        st.text_area(
            "Raw Extracted Text",
            raw_text,
            height=500
        )

    with tab2:

        st.text_area(
            "Cleaned Text",
            cleaned_text,
            height=500
        )

    with tab3:

        st.text_area(
            "Structured Document",
            structured_text,
            height=500
        )

    st.divider()

    st.subheader("Detected Headings")

    if analysis["headings"]:

        for heading in analysis["headings"]:

            st.write(f"• {heading}")

    else:

        st.info("No headings detected.")

    st.divider()

    st.subheader("Top Keywords")

    for word, count in analysis["keywords"]:

        st.write(f"**{word}** ({count})")