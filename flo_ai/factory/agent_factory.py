from flo_ai.state.flo_session import FloSession
from flo_ai.yaml.flo_team_builder import (AgentConfig)
from flo_ai.models.flo_agent import FloAgent

class AgentFactory():

    @staticmethod
    def create(session: FloSession, agent: AgentConfig, tool_map):
        return __create_agent(session, agent, tool_map)


def __create_agent(session: FloSession, agent: AgentConfig, tool_map) -> FloAgent:
    kind = agent.kind # TODO use this to identity binary delegator agent
    tools = [tool_map[tool.name] for tool in agent.tools]
    flo_agent: FloAgent = FloAgent.Builder(
        session,
        agent.name, 
        agent.job,
        tools
    ).build()
    return flo_agent

