import boto3
import streamlit as st
from langchain_aws import ChatBedrock
from langgraph.prebuilt import create_react_agent
from modules.mcp_manager import MCPClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
# from langmem import create_manage_memory_tool, create_search_memory_tool


class AgentManager:
    def create_llm_model(self, **kwargs):
        """Create and return the LLM model instance based on the model ID."""

        # Initialize Bedrock client
        bedrock_client = boto3.client(
            'bedrock-runtime'
        )

        return ChatBedrock(
            client=bedrock_client,
            streaming=True,
            **kwargs
        )

    async def initialize_agent(self, config, global_model_config=None):
        if global_model_config is None:
            global_model_config = {}
        try:
            global_model_config.update(config.get('model',{}))
            st.session_state.model = global_model_config
            llm = self.create_llm_model(**global_model_config)
        except Exception as e:
            st.error(f"Failed to initialize LLM: {e}")
            st.stop()

        # Setup new client
        if 'servers' in config:
            await self.initialize_mcp_client(config['servers'])
        else:
            st.session_state.server = {}
            st.session_state.tools = []

        # checkpointer = InMemorySaver()
        # store = InMemoryStore()
        tools = st.session_state.tools #+ [create_manage_memory_tool(namespace=("memories",)), create_search_memory_tool(namespace=("memories",))]
        st.session_state.agent = create_react_agent(llm, tools=tools, prompt=config['system_prompt'])
                                                    # checkpointer=checkpointer)

    async def initialize_mcp_client(self, config):
        st.session_state.client = MCPClient(config)
        st.session_state.server = st.session_state.client.server_configs
        await st.session_state.client.setup_mcp_client()
        st.session_state.tools = await st.session_state.client.get_tools()
