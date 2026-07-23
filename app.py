import streamlit as st

from modules.pdf_reader import extract_pdf_text
from modules.docx_reader import extract_docx_text

st.set_page_config(
    page_title="GPDI Course Builder",
    page_icon="📚",
    layout="wide"
)

st.title("📚 GPDI Course Builder")

st.subheader("Version 0.2")

uploaded_file = st.file_uploader(
    "Upload a Learner Guide or Facilitator Guide",
    type=["pdf", "docx"]
)

if uploaded_file:

    if uploaded_file.name.endswith(".pdf"):
        extracted_text = extract_pdf_text(uploaded_file)

    elif uploaded_file.name.endswith(".docx"):
        extracted_text = extract_docx_text(uploaded_file)

    else:
        extracted_text = "Unsupported file."

    st.success("Document successfully read!")

    st.subheader("Extracted Text")

    st.text_area(
        "Document Contents",
        extracted_text,
        height=400
    )