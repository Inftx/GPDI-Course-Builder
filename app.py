import streamlit as st

from modules.document_processor import process_document

st.set_page_config(
    page_title="GPDI AI Lecturer Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 GPDI AI Lecturer Assistant")

st.subheader("Version 0.2")

uploaded_file = st.file_uploader(
    "Upload a Learner Guide or Facilitator Guide",
    type=["pdf", "docx"]
)

if uploaded_file:

    try:

        extracted_text = process_document(uploaded_file)

        st.success("Document successfully processed!")

        st.subheader("Extracted Text")

        st.text_area(
            "Document Contents",
            extracted_text,
            height=400
        )

    except Exception as error:

        st.error(error)