import logging
import os
import subprocess
from typing import List, Dict, Any, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for a single MCP server"""

    def __init__(self, name: str,
                 command: str,
                 args: List[str],
                 description: Optional[str] = None,
                 title: Optional[str] = None):
        self.name = name
        self.command = command
        self.args = args
        self.description = description or f"MCP Server: {name}"
        self.title = title

        root_directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Validate command exists
        if not os.path.exists(command):
            raise ValueError(f"Command {command} does not exist for server {name}")

        # Validate script files exist
        for index, script in enumerate(args):
            if root_directory not in script:
                script = os.path.join(root_directory, script)
                args[index] = script
            if not os.path.exists(script):
                raise ValueError(f"Server script {script} does not exist for server {name}")

    def get_config(self) -> Dict[str, Any]:
        """Return the server configuration as a dictionary"""
        return {
            self.name: {
                "command": self.command,
                "args": self.args,
                "description": self.description,
                "transport": "stdio",
                "title": self.title
            }
        }


class MCPClient:
    def __init__(self, server_config):
        self.mcp_initialized = False
        self.server_configs: Dict = {}
        self.add_servers(server_config)
        self.client = None

    def add_server(self,
                   name: str,
                   command: str,
                   args: List[str],
                   description: Optional[str] = None,
                   title: Optional[str] = None):
        """Add an MCP server configuration"""
        try:
            config = MCPServerConfig(name, command, args, description, title)
            self.server_configs.update(config.get_config())
            logger.info(f"Added MCP server configuration: {name}")
        except ValueError as e:
            logger.error(f"Failed to add server {name}: {e}")
            raise

    def add_servers(self, servers: List[Dict[str, Any]]):
        """Add multiple MCP server configurations

        Args:
            servers: List of server configs, each with keys: name, command, args, description (optional)
        """
        for server_config in servers:
            self.add_server(
                name=server_config['name'],
                command=self.which(server_config['command']),
                args=server_config['args'],
                description=server_config.get('description'),
                title=server_config.get('title', server_config['name'])
            )

    async def setup_mcp_client(self):
        """Initialize a MultiServerMCPClient with the provided server configuration."""
        self.client = MultiServerMCPClient(self.server_configs)

    async def get_tools(self) -> List[Any]:
        tools = await self.client.get_tools()
        return tools

    def which(self, program):
        try:
            result = subprocess.run(['which', program], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError(f"'{program}' is not found in the system path.")
