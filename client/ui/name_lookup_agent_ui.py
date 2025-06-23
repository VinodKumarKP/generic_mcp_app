import time

import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager


class NameLookupAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        col1, col2 = st.columns([3, 1])

        with col1:
            with st.form(key="user_input_form", clear_on_submit=True):
                surname = st.text_input("Enter surname", disabled=st.session_state.is_processing, max_chars=20)
                with st.expander("Advanced options"):
                    fmt = st.radio("Select format", ["none", "uppercase", "lowercase", "titlecase", "capitalize"], )

                user_text = st.form_submit_button("Submit", disabled=st.session_state.is_processing)
                if user_text:
                    if surname:
                        user_text = f"Look up name with surname {surname}" + (
                            f" and format it as {fmt}" if fmt != "none" else "")
                    else:
                        st.error("Please enter a surname to look up.")
                        st.session_state.is_processing = False
                        time.sleep(3)
                        st.rerun()
            messages_container = st.container(border=True, height=600)

        with col2:
            progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container
