import streamlit as st

from modules.session_manager import get_current_project
from services.document_upload import (
    DocumentUploadResult,
    process_uploaded_documents,
)


st.set_page_config(
    page_title="Upload Documents",
    page_icon="📄",
)

st.title("📄 Upload Documents")

project = get_current_project()
if not project:
    st.warning("Please select a project from the Project Manager first.")
    st.stop()

st.success(f"Current Project: {project}")
st.divider()

with st.form("document_upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader(
        "Select learner guides, facilitator guides, or supporting documents",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    submitted = st.form_submit_button(
        "Submit Documents",
        type="primary",
    )

if submitted:
    if not uploaded_files:
        st.warning("Select at least one document before submitting.")
        st.session_state["document_upload_results"] = []
    else:
        attempted_uploads = st.session_state.setdefault(
            "document_upload_attempts",
            set(),
        )
        with st.spinner("Processing submitted documents..."):
            st.session_state["document_upload_results"] = (
                process_uploaded_documents(
                    uploaded_files,
                    project,
                    attempted_uploads,
                )
            )

def _show_result(result: DocumentUploadResult) -> None:
    if result.status == "success":
        st.success(f"{result.filename}: {result.message}")
        if result.analysis is not None and result.knowledge is not None:
            with st.expander(f"View details for {result.filename}"):
                _show_document_details(result)
    elif result.status == "failure":
        st.error(f"{result.filename}: {result.message}")
    else:
        st.info(f"{result.filename}: {result.message}")


def _show_document_details(result: DocumentUploadResult) -> None:
    analysis = result.analysis or {}
    knowledge = result.knowledge or {}

    st.subheader("Document statistics")
    columns = st.columns(4)
    metrics = (
        ("Words", analysis.get("word_count", 0)),
        ("Characters", analysis.get("character_count", 0)),
        ("Estimated pages", analysis.get("estimated_pages", 0)),
        ("Reading time", f"{analysis.get('reading_time', 0)} min"),
    )
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)

    raw_tab, clean_tab, structured_tab = st.tabs(
        ["Raw text", "Cleaned text", "Structured document"]
    )
    with raw_tab:
        st.text_area(
            "Raw extracted text",
            value=result.raw_text,
            height=300,
            key=f"{result.filename}_raw",
        )
    with clean_tab:
        st.text_area(
            "Cleaned text",
            value=result.cleaned_text,
            height=300,
            key=f"{result.filename}_clean",
        )
    with structured_tab:
        st.text_area(
            "Structured document",
            value=result.structured_text,
            height=300,
            key=f"{result.filename}_structured",
        )

    st.subheader("Knowledge base summary")
    module = knowledge.get("module")
    if isinstance(module, dict):
        module_label = module.get("code") or module.get("title") or "Not detected"
    else:
        module_label = module or "Not detected"
    topics = knowledge.get("knowledge_topics") or []
    if not isinstance(topics, list):
        topics = [topics]
    total_items = sum(
        len(topic.get("knowledge_items", []))
        for topic in topics
        if isinstance(topic, dict)
        and isinstance(topic.get("knowledge_items", []), list)
    )
    st.write(f"**Knowledge module:** {module_label}")
    st.write(f"**Knowledge topics:** {len(topics)}")
    st.write(f"**Knowledge items:** {total_items}")

    for heading, key in (
        ("Learning outcomes", "learning_outcomes"),
        ("Assessment criteria", "assessment_criteria"),
        ("Knowledge requirements", "knowledge_requirements"),
        ("Practical activities", "practical_activities"),
        ("Workplace activities", "workplace_activities"),
    ):
        values = knowledge.get(key) or []
        if not isinstance(values, list):
            values = [values]
        if values:
            st.markdown(f"**{heading}:**")
            for value in values:
                st.write(f"- {value}")

    warnings = knowledge.get("warnings") or []
    if warnings:
        st.markdown("**Parser warnings:**")
        for warning in warnings:
            st.warning(warning)

    with st.expander("View complete knowledge JSON"):
        st.json(knowledge)


results = st.session_state.get("document_upload_results", [])
if results:
    st.subheader("Processing results")
    for result in results:
        _show_result(result)
