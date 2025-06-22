import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager


class GitOpsAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        with st.form(key="user_input_form", clear_on_submit=True):
            project_url = st.text_input("Project URL", placeholder="Enter the Git repository URL",
                                        disabled=st.session_state.is_processing)
            with st.expander("Advanced options"):
                fmt = st.multiselect("Select analysis",
                                     ["complete",
                                      "commit history",
                                      "file list ",
                                      "programming language",
                                      "repository structure",
                                      "contributor stats"
                                      ])

            user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
            if user_text:
                user_text = f"Clone the project {project_url} and provide " + (
                    f" the following analysis {fmt}" if len(fmt) > 0 else "complete analysis")

        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container
