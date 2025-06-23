from manager.agent_manager import AgentManager

from client.ui.code_remediation_agent_ui import CodeRemediationAgentUI
from client.ui.git_ops_agent_ui import GitOpsAgentUI
from client.ui.name_lookup_agent_ui import NameLookupAgentUI
from client.ui.release_manager_agent_ui import ReleaseManagerAgentUI
from client.ui.ui_manager import StreamlitUIManager
from client.ui.devops_gpt_agent import DevOpsGPTAgentUI


class UIFactory:

    @staticmethod
    def create_ui_manager(agent_name: str, agent_manager: AgentManager):
        if agent_name == "name-lookup":
            return NameLookupAgentUI(agent_manager)
        elif agent_name == "deployment-release-manager-agent":
            return ReleaseManagerAgentUI(agent_manager)
        elif agent_name == "git-ops-agent":
            return GitOpsAgentUI(agent_manager)
        elif agent_name == "devops-code-remediation-agent":
            return CodeRemediationAgentUI(agent_manager)
        elif agent_name == "devops-lookup-agent":
            return DevOpsGPTAgentUI(agent_manager)
        else:
            return StreamlitUIManager(agent_manager)
