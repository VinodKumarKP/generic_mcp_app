import asyncio
import uuid

import streamlit as st


class SessionManager:

    def initialize_state(self):
        # User identification
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())

        if 'loop' not in st.session_state:
            st.session_state.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.loop)
        if 'agent' not in st.session_state:
            st.session_state.agent = None
        if 'tools' not in st.session_state:
            st.session_state.tools = None
        if 'tool_executions' not in st.session_state:
            st.session_state.tool_executions = {}

        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False

        if 'pending_user_text' not in st.session_state:
            st.session_state.pending_user_text = None

        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())

        # Conversation tracking
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = {}

        if st.session_state.user_id not in st.session_state.conversation_history:
            st.session_state.conversation_history[st.session_state.user_id] = []

        # Track the previously selected agent
        if 'previous_agent_key' not in st.session_state:
            st.session_state.previous_agent_key = None

        if 'tool_execution_count' not in st.session_state:
            st.session_state.tool_execution_count = 0

        if 'tool_execution_run_id_list' not in st.session_state:
            st.session_state.tool_execution_run_id_list = []

        if 'model' not in st.session_state:
            st.session_state.model = None

        if 'model_temperature' not in st.session_state:
            st.session_state.model_temperature = 0.0

        if 'previous_model_temperature' not in st.session_state:
            st.session_state.previous_model_temperature = 0.0

        if 'model_max_token' not in st.session_state:
            st.session_state.model_max_token = 1000

        if 'previous_model_max_token' not in st.session_state:
            st.session_state.previous_model_max_token = 1000
