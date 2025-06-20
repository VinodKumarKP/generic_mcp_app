import streamlit as st
from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager


class NameLookupAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        col1, col2 = st.columns([3, 1])

        with col1:
            with st.form(key="user_input_form", clear_on_submit=True):
                surname = st.text_input("Enter surname")
                with st.expander("Advanced options"):
                    fmt = st.radio("Select format", ["none", "uppercase", "lowercase", "titlecase", "capitalize"], )

                user_text = st.form_submit_button("Submit")
                if user_text:
                    user_text = f"Look up name with surname {surname}" + (
                        f" and format it as {fmt}" if fmt != "none" else "")
            messages_container = st.container(border=True, height=600)

        with col2:
            progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container
