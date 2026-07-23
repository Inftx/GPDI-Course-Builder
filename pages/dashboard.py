import streamlit as st

st.title("🏠 Dashboard")

st.markdown("## Welcome to GPDI AI Lecturer Assistant")

col1, col2 = st.columns(2)

with col1:
    st.metric("Projects", "0")

    st.metric("Documents Processed", "0")

with col2:
    st.metric("Lesson Plans", "0")

    st.metric("Assessments", "0")

st.divider()

st.info(
    "Welcome! This dashboard will display statistics and recent projects as the application grows."
)