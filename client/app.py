import datetime
import sys

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from setuptools.package_index import user_agent

from modules.agent_manager import AgentManager
from modules.config_manager import ConfigManager
from modules.session_manager import SessionManager
from modules.ui_manager import StreamlitUIManager
from utils.async_utils import run_async


class ChatApp:
    def __init__(self, config_file="sidebar.yaml"):
        self.config_manager = ConfigManager(config_file=config_file)
        self.session_manager = SessionManager()
        self.ui_manager = StreamlitUIManager()
        self.agent_manager = AgentManager()

        self.session_manager.initialize_state()

    def chat_interface(self):
        self.ui_manager.configure_page()
        agent_name, agent_key, agent_type = self.ui_manager.render_sidebar(self.config_manager.config)
        if st.session_state.previous_agent_key != agent_key:
            st.session_state.conversation_history = {}
            st.session_state.tool_executions = {}
            st.session_state.tool_execution_count = 0
            st.session_state.previous_agent_key = agent_key
            run_async(self.agent_manager.initialize_agent(config=self.config_manager.config['agent'][agent_key],
                                                          global_model_config=self.config_manager.config['model']))

        if st.session_state.agent is None:
            run_async(self.agent_manager.initialize_agent(config=self.config_manager.config['agent'][agent_key],
                                                          global_model_config=self.config_manager.config['model']))

        self.ui_manager.initialize_sidebar_widgets()
        user_text, messages_container, progress_container = self.ui_manager.initialize_user_interface()

        with messages_container:
            self.ui_manager.render_chat_history(st.session_state.user_id, st.session_state.conversation_history)

        with progress_container:
            self.ui_manager.display_tool_execution_history()

        if user_text and not st.session_state.is_processing:
            # Set processing state immediately
            st.session_state.is_processing = True
            st.session_state.pending_user_text = user_text
            st.session_state.tool_executions = {}
            st.session_state.tool_execution_count = 0
            st.rerun()  # Force rerun to update UI state

        if st.session_state.pending_user_text and st.session_state.is_processing:
            user_text = st.session_state.pending_user_text
            st.session_state.pending_user_text = None
            st.session_state.conversation_history[st.session_state.user_id].append(
                {"role": "user", "content": user_text}
            )
            with messages_container.chat_message("user"):
                st.markdown(user_text)

            with st.status("Generating response...", expanded=True) as status:
                st.write("Please wait while agent processes your request. "
                         "Response may take a few minutes depending upon the request.")
                with st.chat_message('assistant'):
                    run_async(self.stream_messages(user_text=user_text, messages_container=messages_container,
                                                   progress_container=progress_container))
                    status.update(label="Response received!", state="complete", expanded=False)
                    st.session_state.is_processing = False

            st.rerun()

    async def stream_messages(self, user_text, messages_container=None, progress_container=None):
        async for chunk in st.session_state.agent.astream(
                {"messages": user_text},
                stream_mode="values",
                config={"configurable": {"thread_id": st.session_state.session_id}}
        ):
            with messages_container:
                tool_count = 0
                for msg in chunk['messages']:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            # Find corresponding ToolMessage
                            tool_output = next(
                                (m.content for m in chunk["messages"]
                                 if isinstance(m, ToolMessage) and
                                 m.tool_call_id == tool_call['id']),
                                None
                            )
                            if tool_output:
                                tool_name = tool_call['name']
                                tool_config = {
                                    "input": tool_call['args'],
                                    "output": tool_output,
                                    "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                st.session_state.tool_executions.update({
                                    tool_name: tool_config
                                })
                                previous_count = st.session_state.tool_execution_count
                                current_count = len(st.session_state.tool_executions)
                                if previous_count != current_count:
                                    st.session_state.tool_execution_count = current_count
                                    with progress_container:
                                        self.ui_manager.display_tool(tool_name=tool_name,
                                                                     tool_config=tool_config,
                                                                     execution_index=current_count)

                    if isinstance(msg, HumanMessage):
                        continue  # Skip human messages
                    if isinstance(msg, AIMessage):
                        stop_reason = None
                        if hasattr(msg, "response_metadata") and msg.response_metadata:
                            stop_reason = msg.response_metadata.get('stop_reason', None)
                        if hasattr(msg, "content") and msg.content and stop_reason == "end_turn":
                            with messages_container.chat_message("assistant"):
                                if isinstance(msg.content, list) and len(msg.content) > 0:
                                    content = msg.content[0]['text']
                                else:
                                    content = msg.content
                                st.session_state.conversation_history[st.session_state.user_id].append(
                                    {"role": "assistant", "content": content}
                                )
                                st.write(content)

    def run(self):
        self.chat_interface()

def argument_parser():
    import argparse
    parser = argparse.ArgumentParser(description="Chat Application")
    parser.add_argument("--config_file", type=str, help="Path to the configuration file")
    return parser.parse_args()


if __name__ == "__main__":
    args = argument_parser()
    app = ChatApp(config_file=args.config_file)
    app.run()
