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
            project_url = st.text_input("Project URL",
                                        placeholder="Enter the Git repository URL" if not st.session_state.is_processing else "Processing... Please wait",
                                        disabled=st.session_state.is_processing,
                                        max_chars=300,
                                        help="Enter the URL of the Git repository to analyze and remediate code issues.")
            with st.expander("Advanced options", expanded=not st.session_state.is_processing):
                analysis = st.multiselect("Select analysis which you want to perform",
                                          ["code issues",
                                           "security analysis",
                                           "performance analysis",
                                           "test coverage",
                                           "documentation",
                                           "code review"
                                           ],
                                          help="Select the type of analysis you want to perform on the codebase.")
                output = st.radio("Select output",
                                  ["result only without remediated code", "result with remediated code"],
                                  index=0,
                                  help="Select whether you want the results only or the results along with the remediated code.")
                fmt = st.radio("Select report format", ["markdown", "tabular"], index=0,
                               help="Select the format for the report output.")
                additional_instructions = st.text_input("Additional instructions (Max 300 chars)",
                                                        placeholder="Enter additional prompt", max_chars=300,
                                                        help="Enter any additional instructions or requirements for the analysis or remediation.")

            try:
                user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
                if user_text:
                    # Validate and sanitize inputs
                    project_url = sanitize_input(project_url)

                    if project_url:
                        user_text = f"Analyze the project {project_url} and provide " + (
                            f" the following analysis {analysis}" if len(analysis) > 0 else "code remediation") + \
                                    f" and provide the results in {fmt} format and {output}." + \
                                    f" {additional_instructions}"
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
