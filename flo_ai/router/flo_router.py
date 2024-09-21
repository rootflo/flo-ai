
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
from flo_ai.models.flo_executable import ExecutableType
import functools

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
    
    def update_reflection_state(self, state: TeamFloAgentState, reflection_agent_name: str):
        tracker = None
        if "reflection_tracker" not in state or state["reflection_tracker"] is None:
            tracker = dict()
        else:
            tracker = state["reflection_tracker"]
      
        if reflection_agent_name in tracker:
            tracker[reflection_agent_name] += 1
        else:
            tracker[reflection_agent_name] = 1
            
        return {
            "reflection_tracker": tracker
        }
    
    def add_reflection_edge(self, workflow: StateGraph, reflection_node: FloNode, nextNode: FloNode):
        to_agent_name = reflection_node.config.to
        retry = reflection_node.config.retry or 1
        reflection_agent_name = reflection_node.name
        next = nextNode.name
        
        workflow.add_node("reflection_counter", functools.partial(self.update_reflection_state, reflection_agent_name=reflection_agent_name))
        workflow.add_edge(reflection_agent_name, "reflection_counter")
        workflow.add_conditional_edges(
            "reflection_counter", 
            self.__get_refelection_routing_fn(retry, reflection_agent_name, to_agent_name, next), 
            { to_agent_name: to_agent_name,  next: next }
        )

    @staticmethod
    def __get_refelection_routing_fn(retries: int, reflection_agent_name, to_agent_name, next):
        def reflection_routing_fn(state: TeamFloAgentState):
            tracker = state["reflection_tracker"]
            if tracker is not None and reflection_agent_name in tracker and tracker[reflection_agent_name] >= retries:
                return next
            return to_agent_name

        return reflection_routing_fn
    

    
        
    