
from abc import ABC, abstractmethod
from flo_ai.state.flo_session import FloSession
from flo_ai.models.flo_team import FloTeam
from flo_ai.yaml.config import TeamConfig, AgentConfig
from flo_ai.models.flo_routed_team import FloRoutedTeam
from flo_ai.models.flo_agent import FloAgent
from flo_ai.state.flo_state import TeamFloAgentState
from flo_ai.models.flo_node import FloNode
from flo_ai.constants.prompt_constants import FLO_FINISH
from langgraph.graph import END,StateGraph
from flo_ai.models.flo_node import FloNode
from flo_ai.helpers.utils import agent_name_from_randomized_name
from flo_ai.models.flo_executable import ExecutableType

class ReflectionRoute:

    def __init__(self, agent_name, reflection_agent_name, retries, next = None):
        self.agent_name = agent_name
        self.reflection_agent_name = reflection_agent_name
        self.retries = retries
        self.next = next

class FloRouter(ABC):

    def __init__(self, session: FloSession, name: str, flo_team: FloTeam, executor, config: TeamConfig = None):
        self.router_name = name
        self.session: FloSession = session
        self.flo_team: FloTeam = flo_team
        self.members = flo_team.members
        self.member_names = [x.name for x in flo_team.members]
        self.type: ExecutableType = flo_team.members[0].type
        self.executor = executor
        self.config = config

    def is_agent_supervisor(self):
        return ExecutableType.isAgent(self.type)
    
    def build_routed_team(self) -> FloRoutedTeam:
        if self.is_agent_supervisor():
            return self.build_agent_graph()
        else:
            return self.build_team_graph()

    @abstractmethod
    def build_agent_graph():
        pass

    @abstractmethod
    def build_team_graph():
        pass

    def build_node(self, flo_agent: FloAgent) -> FloNode:
        node_builder = FloNode.Builder()
        return node_builder.build_from_agent(flo_agent)
    
    def router_fn(self, state: TeamFloAgentState):
        next = state["next"]
        conditional_map = {k: k for k in self.member_names}
        conditional_map[FLO_FINISH] = END
        self.session.append(node=next)
        if self.session.is_looping(node=next):
            return conditional_map[FLO_FINISH]
        return conditional_map[next]
        
    def build_node_for_teams(self, flo_team: FloRoutedTeam):
        node_builder = FloNode.Builder()
        return node_builder.build_from_team(flo_team)
    
    def add_reflection_edge(self, workflow: StateGraph, reflection_node: FloNode, nextNode: FloNode):
        to_agent_name = reflection_node.config.to
        retry = reflection_node.config.retry or 1
        reflection_agent_name = reflection_node.name
        next = nextNode.name
        print(f"Setting router between: {reflection_agent_name} -> {to_agent_name} -> next -> {next}")
        workflow.add_conditional_edges(
            reflection_agent_name, 
            self.__get_refelection_routing_fn(retry, reflection_agent_name, to_agent_name, next), 
            { to_agent_name: to_agent_name,  next: next }
        )

    @staticmethod
    def __get_refelection_routing_fn(retries, reflection_agent_name, to_agent_name, next):
        def reflection_routing_fn(state: TeamFloAgentState):
            if len(state['messages']) > (int(retries)*2)+1 and agent_name_from_randomized_name(state['messages'][-((int(retries)*2)+1)].name) == reflection_agent_name:
                return next
            return to_agent_name

        return reflection_routing_fn

    
        
    