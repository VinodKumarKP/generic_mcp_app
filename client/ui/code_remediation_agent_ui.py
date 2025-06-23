import time

import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager
from utils.validation import sanitize_input


class CodeRemediationAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        prompt_list = []
        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)
        with (st.form(key="user_input_form", clear_on_submit=True)):
            project_url = st.text_input("Project URL", placeholder="Enter the Git repository URL",
                                        disabled=st.session_state.is_processing,
                                        max_chars=300)
            with st.expander("Advanced options"):
                analysis = st.multiselect("Select analysis",
                                          ["code issues",
                                           "security analysis",
                                           "performance analysis",
                                           "test coverage",
                                           "documentation",
                                           "code review"
                                           ])
                output = st.radio("Select output", ["result only without remediated code", "result with remediated code"], index=0)
                fmt = st.radio("Select output format", ["html", "markdown", "json", "text", "tabular"], index=0)

            try:
                user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
                if user_text:
                    # Validate and sanitize inputs
                    project_url = sanitize_input(project_url)

                    if project_url:
                        user_text = f"Analyze the project {project_url} and provide " + (
                            f" the following analysis {analysis}" if len(analysis) > 0 else "code remediation") + \
                                    f" and provide the results in {fmt} format and {output}."
                        prompt_list.append(user_text)
                        prompt_list.append(
                            "Please provide the s3 bucket url of the report")
                        prompt_list.append(
                            "Please provide the s3 bucket url of the remediated code, if the user has requested it.")
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

        return prompt_list, messages_container, progress_container
