import streamlit as st


def set_current_project(project_name):
    st.session_state["current_project"] = project_name


def get_current_project():

    return st.session_state.get(
        "current_project",
        None
    )


def clear_current_project():

    if "current_project" in st.session_state:
        del st.session_state["current_project"]