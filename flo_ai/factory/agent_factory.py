from flo_ai.state.flo_session import FloSession
from flo_ai.yaml.config import (AgentConfig)
from flo_ai.models.flo_agent import FloAgent
from flo_ai.models.flo_llm_agent import FloLLMAgent
from flo_ai.models.flo_reflection_agent import FloReflectionAgent
from flo_ai.models.flo_executable import ExecutableFlo, ExecutableType
from enum import Enum

class AgentKinds(Enum):
    agentic = "agentic"
    llm = "llm"
    tool = "tool"
    function = "function"
    reflexion = "reflexion"

class AgentFactory():

    @staticmethod
    def create(session: FloSession, agent: AgentConfig):
        kind = agent.kind
        tool_map = session.tools
        if kind is not None:
            agent_kind = getattr(AgentKinds, kind, None)
            if agent_kind is None:
                raise ValueError(f"Agent kind cannot be {kind} !")
            match(agent_kind):
                case AgentKinds.llm:
                    return AgentFactory.__create_llm_agent(session, agent)
                case AgentKinds.tool:
                    return AgentFactory.__create_runnable_agent(session, agent)
                case AgentKinds.reflexion:
                    return AgentFactory.__create_reflection_agent(session, agent)
        return AgentFactory.__create_agentic_agent(session, agent, tool_map)

    @staticmethod
    def __create_agentic_agent(session: FloSession, agent: AgentConfig, tool_map) -> FloAgent:
        tools = [tool_map[tool.name] for tool in agent.tools]
        flo_agent: FloAgent = FloAgent.Builder(
            session,
            agent,
            tools
        ).build()
        return flo_agent

    @staticmethod
    def __create_llm_agent(session: FloSession, agent: AgentConfig) -> FloLLMAgent:
        builder = FloLLMAgent.Builder(session, agent)
        llm_agent: FloLLMAgent = builder.build()
        return llm_agent
    
    @staticmethod
    def __create_runnable_agent(session: FloSession, agent: AgentConfig) -> FloLLMAgent:
        runnable = session.tools[agent.tools[0].name]
        return ExecutableFlo(agent.name, runnable, ExecutableType.tool)
    
    @staticmethod
    def __create_reflection_agent(session: FloSession, agent: AgentConfig) -> FloReflectionAgent:
        return FloReflectionAgent.Builder(session, agent).build()