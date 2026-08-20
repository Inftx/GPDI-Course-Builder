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
    st.warning(
        "Please select a project from the Project Manager first."
    )
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

        # --------------------------------------------------
        # SAVE ORIGINAL DOCUMENT
        # --------------------------------------------------

        save_uploaded_file(
            uploaded_file,
            project
        )

        # --------------------------------------------------
        # PROCESS DOCUMENT
        # --------------------------------------------------

        result = process_document(
            uploaded_file
        )

        raw_text = result["raw"]
        cleaned_text = result["clean"]
        structured_text = result["structured"]

        # --------------------------------------------------
        # SAVE CLEANED TEXT
        # --------------------------------------------------

        save_extracted_text(
            cleaned_text,
            uploaded_file.name,
            project
        )

        # --------------------------------------------------
        # SAVE STRUCTURED TEXT
        # --------------------------------------------------

        save_formatted_text(
            structured_text,
            uploaded_file.name,
            project
        )

        # --------------------------------------------------
        # ANALYSE DOCUMENT
        # --------------------------------------------------

        analysis = analyze_document(
            structured_text
        )

        # --------------------------------------------------
        # BUILD KNOWLEDGE BASE
        # --------------------------------------------------

        knowledge = build_knowledge(
            structured_text,
            uploaded_file.name,
            project
        )

        # --------------------------------------------------
        # SAVE METADATA
        # --------------------------------------------------

        save_document_metadata(
            project,
            uploaded_file.name,
            analysis
        )


    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    st.success(
        "✅ Document processed successfully."
    )

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
        "🗂️ Structured Document"
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

        st.info(
            "No headings detected."
        )


    st.divider()


    # --------------------------------------------------
    # TOP KEYWORDS
    # --------------------------------------------------

    st.subheader("🔑 Top Keywords")

    if analysis["keywords"]:

        for word, count in analysis["keywords"]:

            st.write(
                f"**{word}** ({count})"
            )

    else:

        st.info(
            "No keywords detected."
        )


    st.divider()


    # --------------------------------------------------
    # KNOWLEDGE BASE SUMMARY
    # --------------------------------------------------

    st.subheader("🧠 Knowledge Base Summary")


    module = knowledge.get(
        "module",
        {}
    )

    knowledge_topics = knowledge.get(
        "knowledge_topics",
        []
    )

    learning_outcomes = knowledge.get(
        "learning_outcomes",
        []
    )

    assessment_criteria = knowledge.get(
        "assessment_criteria",
        []
    )

    knowledge_requirements = knowledge.get(
        "knowledge_requirements",
        []
    )

    practical_activities = knowledge.get(
        "practical_activities",
        []
    )

    workplace_activities = knowledge.get(
        "workplace_activities",
        []
    )

    warnings = knowledge.get(
        "warnings",
        []
    )


    total_knowledge_items = sum(
        len(topic.get("knowledge_items", []))
        for topic in knowledge_topics
    )


    # --------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Knowledge Module",
            module.get("code") or "Not detected"
        )

    with col2:

        st.metric(
            "Knowledge Topics",
            len(knowledge_topics)
        )

    with col3:

        st.metric(
            "Knowledge Items",
            total_knowledge_items
        )

    with col4:

        st.metric(
            "Warnings",
            len(warnings)
        )


    st.divider()


    # --------------------------------------------------
    # KNOWLEDGE TOPICS
    # --------------------------------------------------

    st.subheader("📚 Knowledge Topics")


    if knowledge_topics:

        for topic in knowledge_topics:

            topic_code = topic.get(
                "code",
                "Unknown"
            )

            topic_title = topic.get(
                "title",
                "Untitled Topic"
            )

            items = topic.get(
                "knowledge_items",
                []
            )

            with st.expander(
                f"{topic_code} - {topic_title}"
            ):

                st.write(
                    f"**Knowledge Items:** {len(items)}"
                )

                for item in items:

                    st.markdown(
                        f"- **{item['code']}** "
                        f"{item['description']}"
                    )

    else:

        st.info(
            "No Knowledge Topics detected."
        )


    # --------------------------------------------------
    # OTHER STRUCTURED INFORMATION
    # --------------------------------------------------

    st.divider()

    st.subheader("📋 Additional Information")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Learning Outcomes",
            len(learning_outcomes)
        )

    with col2:

        st.metric(
            "Assessment Criteria",
            len(assessment_criteria)
        )

    with col3:

        st.metric(
            "Practical Activities",
            len(practical_activities)
        )

    with col4:

        st.metric(
            "Workplace Activities",
            len(workplace_activities)
        )


    # --------------------------------------------------
    # WARNINGS
    # --------------------------------------------------

    if warnings:

        st.divider()

        st.subheader("⚠️ Parser Warnings")

        for warning in warnings:

            st.warning(warning)


    # --------------------------------------------------
    # RAW KNOWLEDGE JSON
    # --------------------------------------------------

    with st.expander(
        "🔍 View Complete Knowledge JSON"
    ):

        st.json(knowledge)