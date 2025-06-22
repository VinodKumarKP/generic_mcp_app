import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager


class CodeRemediationAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        prompt_list = []
        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)
        with (st.form(key="user_input_form", clear_on_submit=True)):
            project_url = st.text_input("Project URL", placeholder="Enter the Git repository URL",
                                        disabled=st.session_state.is_processing)
            with st.expander("Advanced options"):
                analysis = st.multiselect("Select analysis",
                                          ["code remediation",
                                           "security analysis",
                                           "performance analysis",
                                           "test coverage",
                                           "documentation",
                                           "code review"
                                           ])
                fmt = st.radio("Select output format", ["html", "markdown", "json", "text", "tabular"], index=0)

            user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
            if user_text:
                user_text = f"Analyze the project {project_url} and provide " + (
                    f" the following analysis {analysis}" if len(analysis) > 0 else "code remediation") + \
                            f" and provide the results in {fmt} format. "
                prompt_list.append(user_text)
                prompt_list.append("Please provide the s3 bucket url where the results are stored in url format.")

        return prompt_list, messages_container, progress_container
