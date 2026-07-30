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
from modules.knowledge_builder import build_knowledge


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Upload Documents",
    page_icon="📄"
)

st.title("📄 Upload Documents")

# --------------------------------------------------
# CURRENT PROJECT
# --------------------------------------------------

project = get_current_project()

if not project:
    st.warning("Please select a project from the Project Manager first.")
    st.stop()

st.success(f"Current Project: {project}")

st.divider()

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a Learner Guide, Facilitator Guide or Supporting Document",
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

    with st.spinner("Processing document..."):

        # ------------------------------
        # Save Original Document
        # ------------------------------

        save_uploaded_file(
            uploaded_file,
            project
        )

        # ------------------------------
        # Process Document
        # ------------------------------

        result = process_document(
            uploaded_file
        )

        raw_text = result["raw"]
        cleaned_text = result["clean"]
        structured_text = result["structured"]

        # ------------------------------
        # Save Cleaned Text
        # ------------------------------

        save_extracted_text(
            cleaned_text,
            uploaded_file.name,
            project
        )

        # ------------------------------
        # Save Structured Text
        # ------------------------------

        save_formatted_text(
            structured_text,
            uploaded_file.name,
            project
        )

        # ------------------------------
        # Analyse Document
        # ------------------------------

        analysis = analyze_document(
            structured_text
        )

        # ------------------------------
        # Build Knowledge Base
        # ------------------------------

        knowledge = build_knowledge(
            structured_text,
            uploaded_file.name,
            project
        )

        # ------------------------------
        # Save Metadata
        # ------------------------------

        save_document_metadata(
            project,
            uploaded_file.name,
            analysis
        )

    st.success("✅ Document processed successfully.")

    st.divider()

    # --------------------------------------------------
    # DOCUMENT STATISTICS
    # --------------------------------------------------

    st.subheader("📊 Document Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Words",
            analysis["word_count"]
        )

    with col2:
        st.metric(
            "Characters",
            analysis["character_count"]
        )

    with col3:
        st.metric(
            "Estimated Pages",
            analysis["estimated_pages"]
        )

    with col4:
        st.metric(
            "Reading Time",
            f"{analysis['reading_time']} min"
        )

    st.divider()

    # --------------------------------------------------
    # DOCUMENT TABS
    # --------------------------------------------------

    raw_tab, clean_tab, structured_tab = st.tabs([
        "📄 Raw Text",
        "🧹 Cleaned Text",
        "🧠 Structured Document"
    ])

    with raw_tab:

        st.text_area(
            label="Raw Extracted Text",
            value=raw_text,
            height=500
        )

    with clean_tab:

        st.text_area(
            label="Cleaned Text",
            value=cleaned_text,
            height=500
        )

    with structured_tab:

        st.text_area(
            label="Structured Document",
            value=structured_text,
            height=500
        )

    st.divider()

    # --------------------------------------------------
    # DETECTED HEADINGS
    # --------------------------------------------------

    st.subheader("📑 Detected Headings")

    if analysis["headings"]:

        for heading in analysis["headings"]:

            st.write(f"• {heading}")

    else:

        st.info("No headings detected.")

    st.divider()

    # --------------------------------------------------
    # TOP KEYWORDS
    # --------------------------------------------------

    st.subheader("🔑 Top Keywords")

    if analysis["keywords"]:

        for word, count in analysis["keywords"]:

            st.write(f"**{word}** ({count})")

    else:

        st.info("No keywords detected.")

    st.divider()

    # --------------------------------------------------
    # KNOWLEDGE BASE
    # --------------------------------------------------

    st.subheader("🧠 Knowledge Base Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Modules",
            len(knowledge["modules"])
        )

    with col2:
        st.metric(
            "Learning Outcomes",
            len(knowledge["learning_outcomes"])
        )

    with col3:
        st.metric(
            "Assessment Criteria",
            len(knowledge["assessment_criteria"])
        )

    with st.expander("View Knowledge Base"):

        st.json(knowledge)