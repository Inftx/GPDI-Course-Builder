import streamlit as st

from modules.project_manager import (
    create_project,
    get_projects
)

from modules.session_manager import (
    set_current_project,
    get_current_project
)

# --------------------------------------------------
# PAGE TITLE
# --------------------------------------------------

st.title("📁 Project Manager")

st.write("Create and manage educational projects.")

st.divider()

# --------------------------------------------------
# CREATE PROJECT
# --------------------------------------------------

st.subheader("Create New Project")

project_name = st.text_input(
    "Project Name"
)

if st.button("Create Project"):

    if project_name.strip():

        create_project(project_name)

        st.success(f"Project '{project_name}' created successfully!")

        st.rerun()

    else:

        st.warning("Please enter a project name.")

st.divider()

# --------------------------------------------------
# PROJECT LIST
# --------------------------------------------------

projects = get_projects()

st.subheader("Available Projects")

if projects:

    selected_project = st.selectbox(
        "Select Project",
        projects
    )

    if st.button("Open Project"):

        set_current_project(selected_project)

        st.success(f"{selected_project} is now the active project.")

else:

    st.info("No projects have been created yet.")

st.divider()

# --------------------------------------------------
# CURRENT PROJECT
# --------------------------------------------------

current = get_current_project()

st.subheader("Current Project")

if current:

    st.success(current)

else:

    st.warning("No project selected.")