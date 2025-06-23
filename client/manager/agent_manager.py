import streamlit as st
from langchain_aws import ChatBedrock
from langchain_aws.agents.base import BedrockAgentsRunnable
from langgraph.prebuilt import create_react_agent
from manager.aws_client_manager import AWSClientManager
from manager.mcp_manager import MCPClient


class AgentManager:
    def __init__(self, aws_clients: AWSClientManager, ):
        """
        Initialize the Bedrock Agent Manager.

        Args:
            aws_clients: Initialized AWS client manager
        """
        self.bedrock_agent_runtime_client = aws_clients.bedrock_agent_runtime_client
        self.bedrock_agent_client = aws_clients.bedrock_agent_client
        self.bedrock_runtime_client = aws_clients.bedrock_runtime_client

    def get_aws_bedrock_agent_list(self):
        """
        Retrieve a list of available agents.

        Returns:
            list: List of agent dictionaries
        """
        response = self.bedrock_agent_client.list_agents()
        return [agent['agentName'] for agent in response['agentSummaries']]

    async def get_aws_bedrock_agent_id(self, agent_name: str) -> str:
        """
        Retrieve the agent ID for a given agent name.

        Args:
            agent_name: Name of the agent to find

        Returns:
            str: Agent ID

        Raises:
            ValueError: If the agent is not found
        """
        response = self.bedrock_agent_client.list_agents()

        agent_id = None
        if 'agentSummaries' in response:
            for agent in response['agentSummaries']:
                if agent_name in agent['agentName']:
                    agent_id = agent['agentId']
                    break

        if agent_id is None:
            raise ValueError(f"Agent {agent_name} not found")

        return agent_id

    async def get_aws_bedrock_agent_alias_id(self, agent_id: str, agent_name: str) -> str:
        """
        Retrieve the alias ID for a given agent.

        Args:
            agent_id: ID of the agent
            agent_name: Name of the agent (for error reporting)

        Returns:
            str: Agent alias ID

        Raises:
            ValueError: If the agent alias is not found
        """
        response = self.bedrock_agent_client.list_agent_aliases(agentId=agent_id)

        alias_id = None
        if 'agentAliasSummaries' in response:
            for alias in response['agentAliasSummaries']:
                if 'latest' in alias['agentAliasName']:
                    alias_id = alias['agentAliasId']
                    break

        if alias_id is None:
            raise ValueError(f"Alias for agent {agent_name} not found")

        return alias_id

    def create_llm_model(self, **kwargs):
        """Create and return the LLM model instance based on the model ID."""
        return ChatBedrock(
            client=self.bedrock_runtime_client,
            streaming=True,
            **kwargs
        )

    async def initialize_agent(self, agent_key, config, global_model_config=None):
        if global_model_config is None:
            global_model_config = {}
        try:
            global_model_config.update(config.get('model', {}))
            global_model_config['temperature'] = st.session_state.model_temperature
            global_model_config['max_tokens'] = st.session_state.model_max_token
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

        if config['type'] == 'mcp':
            st.session_state.agent = create_react_agent(llm, tools=st.session_state.tools,
                                                        prompt=config['system_prompt'])
        elif config['type'] == 'bedrock':
            agent_id = await self.get_aws_bedrock_agent_id(agent_name=agent_key)
            agent_alias_id = await self.get_aws_bedrock_agent_alias_id(agent_id=agent_id,
                                                                       agent_name=agent_key)
            st.session_state.agent = self.create_bedrock_agent_runnable(
                agent_id=agent_id,
                agent_alias_id=agent_alias_id
            )

    async def initialize_mcp_client(self, config):
        st.session_state.client = MCPClient(config)
        st.session_state.server = st.session_state.client.server_configs
        await st.session_state.client.setup_mcp_client()
        st.session_state.tools = await st.session_state.client.get_tools()

    def create_bedrock_agent_runnable(self,
                                      agent_id: str,
                                      agent_alias_id: str = "TSTALIASID",
                                      region_name: str = "us-east-2"
                                      ) -> BedrockAgentsRunnable:
        """
        Create and configure a BedrockAgentsRunnable instance

        Args:
            agent_id: The ID of your Bedrock agent
            agent_alias_id: The alias ID for the agent (default: TSTALIASID for test)
            region_name: AWS region where your agent is deployed

        Returns:
            BedrockAgentsRunnable instance
        """
        try:
            # Create the runnable with your agent configuration
            bedrock_agent = BedrockAgentsRunnable(
                agent_id=agent_id,
                agent_alias_id=agent_alias_id,
                region_name=region_name,
                client=self.bedrock_agent_runtime_client
            )

            return bedrock_agent

        except Exception as e:
            print(f"❌ Error creating BedrockAgentsRunnable: {e}")
            raise
