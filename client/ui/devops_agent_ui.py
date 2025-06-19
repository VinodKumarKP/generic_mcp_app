from typing_extensions import override

from client.ui.ui_manager import StreamlitUIManager
import streamlit as st


class DevOpsAgentUI(StreamlitUIManager):

    @override
    def initialize_user_interface(self):
        user_text = st.chat_input(
            "Enter your prompt here" if not st.session_state.is_processing else "Processing... Please wait",
            disabled=st.session_state.is_processing,
            key="chat_input"
        )

        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container