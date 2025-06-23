import time

import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager
from utils.validation import sanitize_input


class GitOpsAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        with st.form(key="user_input_form", clear_on_submit=True):
            project_url = st.text_input("Project URL",
                                        placeholder="Enter the Git repository URL" if not st.session_state.is_processing else "Processing... Please wait",
                                        disabled=st.session_state.is_processing, max_chars=300)
            with st.expander("Advanced options", expanded=not st.session_state.is_processing):
                analysis = st.multiselect("Select analysis",
                                          ["complete",
                                           "commit history",
                                           "file list ",
                                           "programming language",
                                           "repository structure",
                                           "contributor stats"
                                           ])
                fmt = st.radio("Select output format", ["html", "markdown", "json", "text", "tabular"], index=0)

            user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)

            try:
                if user_text:
                    project_url = sanitize_input(project_url)
                    if project_url:
                        user_text = f"Clone the project {project_url} and provide " + (
                            f" the following analysis {analysis}" if len(analysis) > 0 else "complete analysis") + \
                                    f" and provide the results in {fmt} format. "
                    else:
                        st.error("Please enter a valid project URL.")
                        st.session_state.is_processing = False
                        time.sleep(3)
                        st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.is_processing = False
                time.sleep(3)
                st.rerun()

        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container
