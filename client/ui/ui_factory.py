from client.ui.devops_agent_ui import DevOpsAgentUI
from client.ui.name_lookup_agent_ui import NameLookupAgentUI
from client.ui.ui_manager import StreamlitUIManager


class UIFactory:

    @staticmethod
    def create_ui_manager(agent_name: str):
        if agent_name == "name-lookup":
            return NameLookupAgentUI()
        elif agent_name == "deployment-release-manager-agent":
            return DevOpsAgentUI()
        else:
            return StreamlitUIManager()