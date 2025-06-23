import json
import os
from typing import Dict

import streamlit as st
from manager.agent_manager import AgentManager

from utils.constants import Constants


class StreamlitUIManager:

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager

    def configure_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="AWS Bedrock Chat",
            page_icon="🤖",
            layout="wide"
        )
        self.load_css()

    def configure_header(self, agent_name: str):
        st.header(f"💬 Chat with {agent_name.title()} Agent")

    def _render_sidebar_header(self):
        """Render professional sidebar header."""
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="margin: 0; color: var(--primary-blue); font-size: 1.5rem;">
                ⚡ AI Assistant
            </h1>
            <p style="margin: 0.5rem 0 0 0; color: var(--dark-text-muted); font-size: 0.875rem;">
                Powered by AWS Bedrock
            </p>
        </div>
        """, unsafe_allow_html=True)

    def _filter_agent_options(self, option_list: Dict[str, str], search_term: str) -> Dict[str, str]:
        """Filter agent options based on search term."""
        if not search_term:
            return option_list

        search_lower = search_term.lower()
        return {
            name: value for name, value in option_list.items()
            if search_lower in name.lower() or search_lower in value.lower()
        }

    def _render_selected_agent(self, config: Dict):
        with st.container(border=True):
            agent_list = self.agent_manager.get_aws_bedrock_agent_list()

            option_list = {}
            option_list.update(
                {values['name']: f"{key}:{values['name']}:{values['type']}:{values.get('order', 100)}" for key, values in
                 config['agent'].items() if
                 values['type'] == 'mcp'})
            option_list.update({values['name']: f"{key}:{agent}:{values['type']}:{values.get('order', 100)}"
                                for agent in agent_list for key, values in config['agent'].items() if key in agent})

            option_list = dict(sorted(option_list.items(), key=lambda item: int(item[1].split(":")[-1])))

            search_term = st.text_input(
                "🔍 Search agents...",
                placeholder="Type to filter agents",
                key="agent_search",
                help="Search by agent name or type"
            )

            # Filter options based on search
            filtered_options = self._filter_agent_options(option_list, search_term)

            if not filtered_options:
                st.warning("No agents match your search criteria.")
                return None, None, None

            selected_agent = st.selectbox(
                "Select Agent",
                options=list(filtered_options.keys()),
                disabled=st.session_state.get('is_processing', False),
                help="Choose an AI agent to interact with",
                key="agent_selector"
            )
            st.divider()

            if selected_agent:
                agent_key = option_list[selected_agent].split(":")[0]
                agent_type = option_list[selected_agent].split(":")[2]
                agent_name = option_list[selected_agent].split(":")[1]

                with st.expander("ⓛ  Instructions", expanded=False):
                    st.markdown(config['agent'][agent_key]['instructions'], unsafe_allow_html=True)

                return agent_name, agent_key, agent_type
            else:
                st.error("No agent selected. Please select an agent to continue.")
                return None, None, None

    def render_sidebar(self, config: Dict):
        """Render the sidebar with a title."""
        st.sidebar.title("⚡ AI Assistant")

        with st.sidebar:
            agent_name, agent_key, agent_type = self._render_selected_agent(config=config)

        return agent_name, agent_key, agent_type

    def model_info_container(self, config, global_model_config):
        if st.session_state.model:
            with st.sidebar:
                st.divider()
                with st.sidebar.expander("⚙️  Basic config", expanded=False):
                    st.subheader("Model Id: " + config.get('mode_id', global_model_config.get('model_id', '')))
                    st.session_state.previous_model_max_token = st.session_state.model_max_token
                    st.session_state.model_max_token = st.number_input("Max tokens",
                                                                       min_value=10,
                                                                       max_value=10240,
                                                                       value=config.get('model', {}).get('max_tokens',
                                                                                                         global_model_config.get(
                                                                                                             'max_tokens',
                                                                                                             4096)),
                                                                       step=512,
                                                                       disabled=st.session_state.is_processing,
                                                                       help="Maximum number of tokens to generate. A word is generally 2-3 tokens")
                    st.session_state.previous_model_temperature = st.session_state.model_temperature
                    st.session_state.model_temperature = st.slider("Temperature", 0.0, 1.0, step=0.05,
                                                                   value=config.get('model', {}).get('temperature',
                                                                                                     global_model_config.get(
                                                                                                         'temperature',
                                                                                                         1.0)),
                                                                   disabled=st.session_state.is_processing,
                                                                   help="Higher values make the output more random, lower values make it more deterministic")

    def server_info_container(self):
        if st.session_state.server:
            with st.sidebar:
                st.divider()
                st.text("Connected to MCP Servers:")
                with st.expander(f"Available Server ({len(st.session_state.server)})", expanded=False):
                    for name, config in st.session_state.server.items():
                        with st.popover(f"**{config.get('title', name)}**", use_container_width=True):
                            st.markdown(f"**Description:** {config['description']}")

    def tool_info_container(self):
        if st.session_state.tools:
            with st.sidebar:
                with st.expander(f"Available Tools ({len(st.session_state.tools)})", expanded=False):
                    for tool in st.session_state.tools:
                        with st.popover(f"{tool.name}", use_container_width=True):
                            st.markdown(f"**Tool:** {tool.name}")
                            st.markdown(f"**Description:** {tool.description}")

    def render_chat_history(self, user_id: str, conversation_history: Dict):
        """
        Render the chat history for the current user.

        Args:
            user_id: Current user ID
            conversation_history: Dictionary containing all conversation histories
        """
        if user_id in conversation_history:
            for message in conversation_history[user_id]:
                role = message["role"]
                content = message["content"]

                if role == "user":
                    st.chat_message("user", avatar=Constants.USER_AVATAR).markdown(content, unsafe_allow_html=True)
                else:
                    st.chat_message("assistant", avatar=Constants.ASSISTANT_AVATAR).write(content,
                                                                                          unsafe_allow_html=True)

    def load_css(self):
        """Load CSS styles for the application."""

        directory_name = os.path.dirname(__file__)
        config_path = os.path.join(os.path.dirname(directory_name), 'style.css')

        with open(config_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    def display_tool(self, tool_name, tool_config, execution_index):
        st.markdown(f"### Execution #{execution_index}: `{tool_name}`")
        st.markdown(f"**Input:** ```json{json.dumps(tool_config['input'])}```")
        st.markdown(f"**Output:** ```json{json.dumps(tool_config['output'])}```")
        st.markdown(f"**Time:** {tool_config['timestamp']}")
        st.divider()

    def display_tool_execution_history(self):
        if st.session_state.tool_executions:
            for i, (tool_name, tool_config) in enumerate(st.session_state.tool_executions.items()):
                self.display_tool(tool_name=tool_name,
                                  tool_config=tool_config,
                                  execution_index=i + 1)

    def initialize_user_interface(self):
        user_text = st.chat_input(
            "Enter your prompt here" if not st.session_state.is_processing else "Processing... Please wait",
            disabled=st.session_state.is_processing,
            key="chat_input",
            max_chars=100
        )

        messages_container = st.container(border=True, height=600)
        progress_container = st.expander("Progress", expanded=False)

        return user_text, messages_container, progress_container

    def initialize_sidebar_widgets(self, config: Dict, global_model_config: Dict):
        self.model_info_container(config=config, global_model_config=global_model_config)
        self.server_info_container()
        self.tool_info_container()
