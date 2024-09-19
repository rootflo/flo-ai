
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
from typing import List, Tuple
from flo_ai.models.flo_node import FloNode
from flo_ai.helpers.utils import agent_name_from_randomized_name
class FloRouter(ABC):

    def __init__(self, session: FloSession, name: str, flo_team: FloTeam, executor, config: TeamConfig = None):
        self.router_name = name
        self.session: FloSession = session
        self.flo_team: FloTeam = flo_team
        self.members = flo_team.members
        self.member_names = [x.name for x in flo_team.members]
        self.type = flo_team.members[0].type
        self.executor = executor
        self.config = config

    def is_agent_supervisor(self):
        return self.type == "agent"
    
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

    def build_node(self, flo_agent: FloAgent):
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
    
    def differentiate_nodes(self, flo_nodes: List[FloNode], agents: List[AgentConfig] | None) -> Tuple[List[FloNode], List[FloNode]]:
        node_dict = {}
        agent_nodes = []
        reflection_nodes = []
        
        for agent in agents:
            if agent.reflection:
                node_dict['reflection_nodes'] = agent.name
            else:
                node_dict['agent_nodes'] = agent.name

        for node in flo_nodes:
            node_name = agent_name_from_randomized_name(node.name)
            if node_name in node_dict['reflection_nodes']:
                reflection_nodes.append(node)
            elif node_name in node_dict['agent_nodes']:
                agent_nodes.append(node)

        return agent_nodes, reflection_nodes
        
    
    def build_reflection_routes(self, workflow: StateGraph, agents: List[AgentConfig] | None, reflection_nodes: List[FloNode]):
        if len(reflection_nodes) == 0:
            return
        
        reflection_routes = self.__get_reflection_routes(agents)

        for reflection in reflection_routes:
            parent_node = reflection['nodes'][0]
            reflection_node = reflection['nodes'][1]
            next = END if reflection['next'] == 'END' else reflection['next']

            workflow.add_conditional_edges(parent_node, self.__get_refelection_routing_fn(reflection['retries'], parent_node, reflection_node, next), {reflection_node: reflection_node, next: next})
            workflow.add_edge(reflection_node, parent_node)

    @staticmethod
    def __get_refelection_routing_fn(retries, parent_node, reflection_node, next):
        def reflection_routing_fn(state: TeamFloAgentState):
            if len(state['messages']) > (int(retries)*2)+1 and agent_name_from_randomized_name(state['messages'][-((int(retries)*2)+1)].name) == parent_node:
                return next
            return reflection_node

        return reflection_routing_fn


    @staticmethod
    def __get_reflection_routes(agents: List[AgentConfig] | None):
        reflection_routes = []

        for agent in agents:
            if agent.reflection:
                route = {}
                route['nodes'] = [agent.reflection.node, agent.name]
                route['retries'] = agent.reflection.retries
                route['next'] = agent.reflection.next
                reflection_routes.append(route)

        return reflection_routes
        
    