import argparse
import datetime
import logging
import os

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from client.ui.ui_factory import UIFactory
from client.ui.ui_manager import StreamlitUIManager
from manager.agent_manager import AgentManager
from manager.aws_client_manager import AWSClientManager
from manager.config_manager import ConfigManager
from manager.session_manager import SessionManager
from utils.async_utils import run_async
from utils.constants import Constants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatApp:
    def __init__(self, config_file="sidebar.yaml"):
        # Use a secure default configuration path
        default_config_path = os.path.join(
            os.path.dirname(__file__),
            'config',
            'sidebar.yaml'
        )


        self.config_manager = ConfigManager(config_file=config_file)
        self.session_manager = SessionManager()
        self.aws_manager = AWSClientManager()
        self.agent_manager = AgentManager(aws_clients=self.aws_manager)
        self.ui_manager = StreamlitUIManager(agent_manager=self.agent_manager)

        self.session_manager.initialize_state()

    def chat_interface(self):
        self.ui_manager.configure_page()
        agent_name, agent_key, agent_type = self.ui_manager.render_sidebar(self.config_manager.config)

        self.ui_manager = UIFactory().create_ui_manager(agent_name=agent_key, agent_manager=self.agent_manager)

        if st.session_state.previous_agent_key != agent_key or \
                st.session_state.previous_model_temperature != st.session_state.model_temperature or \
                   st.session_state.previous_model_max_token != st.session_state.model_max_token:
            st.session_state.agent = None
            st.session_state.model = None
            st.session_state.conversation_history = {} if st.session_state.previous_agent_key != agent_key else st.session_state.conversation_history
            st.session_state.tool_executions = {} if st.session_state.previous_agent_key != agent_key else st.session_state.tool_executions
            st.session_state.tool_execution_count = 0 if st.session_state.previous_agent_key != agent_key else st.session_state.tool_execution_count
            st.session_state.previous_agent_key = agent_key
            self.session_manager.initialize_state()
            run_async(self.agent_manager.initialize_agent(agent_key=agent_key,
                                                          config=self.config_manager.config['agent'][agent_key],
                                                          global_model_config=self.config_manager.config['model']))

        if st.session_state.agent is None:
            run_async(self.agent_manager.initialize_agent(config=self.config_manager.config['agent'][agent_key],
                                                          global_model_config=self.config_manager.config['model']))

        self.ui_manager.initialize_sidebar_widgets(config=self.config_manager.config['agent'][agent_key],
                                                          global_model_config=self.config_manager.config['model'])
        user_text, messages_container, progress_container = self.ui_manager.initialize_user_interface()

        prompt_list = []
        if isinstance(user_text, str):
            prompt_list.append(user_text)
        else:
            prompt_list = user_text

        with messages_container:
            self.ui_manager.render_chat_history(st.session_state.user_id, st.session_state.conversation_history)

        with progress_container:
            self.ui_manager.display_tool_execution_history()

        if user_text and not st.session_state.is_processing:
            # Set processing state immediately
            st.session_state.is_processing = True
            st.session_state.pending_user_text = prompt_list
            st.session_state.tool_executions = {}
            st.session_state.tool_execution_count = 0
            st.rerun()  # Force rerun to update UI state

        if st.session_state.pending_user_text and st.session_state.is_processing:
            prompt_list = st.session_state.pending_user_text
            st.session_state.pending_user_text = None
            st.session_state.conversation_history[st.session_state.user_id].append(
                {"role": "user", "content": '\n'.join(prompt_list)}
            )
            with messages_container.chat_message("user", avatar=Constants.USER_AVATAR):
                st.markdown('\n'.join(prompt_list))

            with messages_container:
                with st.status("Generating response...", expanded=True) as status:
                    st.write("Please wait while agent processes your request. "
                             "Response may take a few minutes depending upon the request.")
                    conversation_history = ''
                    for message in reversed(st.session_state.conversation_history[st.session_state.user_id]):
                        if message['role'] == 'assistant':
                            conversation_history += message['content'] + "\n"
                            break

                    with st.chat_message('assistant', avatar=Constants.ASSISTANT_AVATAR):
                        for prompt in prompt_list:
                            if self.config_manager.config['agent'][agent_key]['type'] == 'mcp':
                                user_text = conversation_history + "\n" + '\n'.join(prompt)
                                run_async(
                                    self.stream_messages(user_text=user_text, messages_container=messages_container,
                                                         progress_container=progress_container))
                            elif self.config_manager.config['agent'][agent_key]['type'] == 'bedrock':
                                run_async(self.stream_bedrock_messages(user_text=prompt,
                                                                       messages_container=messages_container,
                                                                       progress_container=progress_container))
                        status.update(label="Response received!", state="complete", expanded=False)
                        st.session_state.is_processing = False

                st.rerun()

    async def stream_bedrock_messages(self, user_text, messages_container=None, progress_container=None):
        input_dict = {
            "input": user_text,
            "chat_history": [],
            "session_id": st.session_state.session_id
        }
        config = {"session_id": st.session_state.session_id}
        runnable_config = RunnableConfig(**config)

        # Try with session configuration
        response = st.session_state.agent.invoke(
            input_dict,
            session_id=st.session_state.session_id,
            configurable=runnable_config
        )
        with messages_container.chat_message("assistant", avatar=Constants.ASSISTANT_AVATAR):
            st.session_state.conversation_history[st.session_state.user_id].append(
                {"role": "assistant", "content": response.messages[0].content}
            )
            st.markdown(response.messages[0].content, unsafe_allow_html=True)

    async def stream_messages(self, user_text, messages_container=None, progress_container=None):
        try:
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
                            tool_id = msg.id
                            if hasattr(msg, "content") and msg.content and stop_reason in ["end_turn", "max_tokens",
                                                                                           "tool_use"]:
                                if isinstance(msg.content, list) and len(msg.content) > 0:
                                    content = str(msg.content[0].get('text', '')).strip()
                                else:
                                    content = str(msg.content).strip()

                                if tool_id and tool_id not in st.session_state.tool_execution_run_id_list:
                                    if len(content) > 0:
                                        with messages_container.chat_message("assistant",
                                                                             avatar=Constants.ASSISTANT_AVATAR):
                                            st.session_state.tool_execution_run_id_list.append(tool_id)
                                            if len(content) > 0:
                                                st.session_state.conversation_history[st.session_state.user_id].append(
                                                    {"role": "assistant", "content": content}
                                                )
                                                st.markdown(content, unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Stream messages error: {e}")
            st.error(f"Error processing messages: {e}")

    def run(self):
        try:
            self.chat_interface()
        except Exception as e:
            logger.error(f"Application run error: {e}")
            st.error(f"Critical application error: {e}")


def argument_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Secure Chat Application")
    parser.add_argument(
        "--config_file",
        type=str,
        help="Path to the configuration file",
        default=None
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = argument_parser()
        app = ChatApp(config_file=args.config_file)
        app.run()
    except Exception as e:
        logging.error(f"Startup error: {e}")
        print(f"Failed to start application: {e}")
