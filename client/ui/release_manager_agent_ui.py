import time

import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager


class ReleaseManagerAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        prompt_list = []
        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)
        with (st.form(key="user_input_form", clear_on_submit=True)):
            project_url = st.text_input("Project Name",
                                        placeholder="Enter the Project Name" if not st.session_state.is_processing else "Processing... Please wait",
                                        disabled=st.session_state.is_processing)
            with st.expander("Advanced options", expanded=not st.session_state.is_processing):
                analysis = st.radio("Select analysis",
                                    ["summary",
                                     "detailed"
                                     ])
                fmt = st.radio("Select output format", ["html", "markdown", "json", "text", "tabular"], index=0)
                additional_instructions = st.text_input("Additional instructions",
                                                        placeholder="Enter additional prompt")

            user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
            try:
                if user_text:
                    if project_url:
                        user_text = f"Analyze the project {project_url} and provide " + (
                            f" {analysis} analysis of the report" if len(analysis) > 0 else "summary") + \
                                    f" and provide the results in {fmt} format. " + \
                                    f" {additional_instructions}"
                        prompt_list.append(user_text)
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
