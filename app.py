import streamlit as st

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="GPDI AI Lecturer Assistant",
    page_icon="📚",
    layout="wide"
)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("📚 GPDI AI Lecturer Assistant")

st.caption("Version 1.0")

st.divider()

# --------------------------------------------------
# WELCOME
# --------------------------------------------------

st.header("Welcome")

st.write("""
Welcome to the GPDI AI Lecturer Assistant.

This application is designed to help lecturers and instructional designers:

• Manage educational projects

• Upload learner and facilitator guides

• Analyse qualification documents

• Generate AI lesson plans

• Create facilitator guides

• Generate assessments

• Export teaching material
""")

st.divider()

# --------------------------------------------------
# SYSTEM STATUS
# --------------------------------------------------

st.subheader("System Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("Project System")

with col2:
    st.success("Document Processing")

with col3:
    st.info("AI Generator (Coming Soon)")

st.divider()

st.info(
    "Use the navigation menu on the left to access each section of the application."
)