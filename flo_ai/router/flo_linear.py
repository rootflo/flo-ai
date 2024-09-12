from flo_ai.yaml.flo_team_builder import RouterConfig, TeamConfig, AgentConfig
from flo_ai.router.flo_router import FloRouter
from langgraph.graph import StateGraph, END, START
from flo_ai.state.flo_state import TeamFloAgentState
from flo_ai.models.flo_routed_team import FloRoutedTeam
from flo_ai.models.flo_team import FloTeam
from flo_ai.state.flo_session import FloSession
from flo_ai.helpers.utils import agent_name_from_randomized_name, randomize_name
from typing import List, Tuple
from flo_ai.models.flo_node import FloNode
class FloLinear(FloRouter):

    def __init__(self, session: FloSession, flo_team: FloTeam, config: TeamConfig):
        super().__init__(session=session, name=randomize_name(config.name),
                          flo_team=flo_team, executor=None, config=config)
        self.router_config = config.router
    
    def build_agent_graph(self):
        flo_nodes = [self.build_node(flo_agent) for flo_agent in self.members]
        flo_agent_nodes: List[FloNode] 
        flo_reflection_nodes: List[FloNode] 
        flo_agent_nodes, flo_reflection_nodes = self.differentiate_nodes(flo_nodes, self.config.agents)
        
        workflow = StateGraph(TeamFloAgentState)
        
        for flo_node in flo_nodes:
            agent_name = agent_name_from_randomized_name(flo_node.name)
            workflow.add_node(agent_name, flo_node.func)

        self.build_reflection_routes(workflow, self.config.agents, flo_reflection_nodes)
            
        if self.router_config.edges is None:
            start_node_name = agent_name_from_randomized_name(flo_agent_nodes[0].name)
            end_node_name = agent_name_from_randomized_name(flo_agent_nodes[-1].name)
            workflow.add_edge(START, start_node_name)
            for i in range(len(flo_agent_nodes) - 1):
                agent1_name = agent_name_from_randomized_name(flo_agent_nodes[i].name)
                agent2_name = agent_name_from_randomized_name(flo_agent_nodes[i+1].name)
                workflow.add_edge(agent1_name, agent2_name)
            workflow.add_edge(end_node_name, END)
        else:
            workflow.add_edge(START, self.router_config.start_node)
            for edge in self.router_config.edges:
                workflow.add_edge(edge[0], edge[1])
            workflow.add_edge(self.router_config.end_node, END)

        workflow_graph = workflow.compile()
    
        return FloRoutedTeam(self.flo_team.name, workflow_graph)

    def build_team_graph(self):
        flo_team_entry_chains = [self.build_node_for_teams(flo_agent) for flo_agent in self.members]
        # Define the graph.
        super_graph = StateGraph(TeamFloAgentState)
        # First add the nodes, which will do the work
        for flo_team_chain in flo_team_entry_chains:
            agent_name = agent_name_from_randomized_name(flo_team_chain.name)
            super_graph.add_node(agent_name, flo_team_chain.func)

        if self.router_config.edges is None:
            start_node_name = agent_name_from_randomized_name(flo_team_entry_chains[0].name)
            end_node_name = agent_name_from_randomized_name(flo_team_entry_chains[-1].name)
            super_graph.add_edge(START, start_node_name)
            for i in range(len(flo_team_entry_chains) - 1):
                agent1_name = agent_name_from_randomized_name(flo_team_entry_chains[i].name)
                agent2_name = agent_name_from_randomized_name(flo_team_entry_chains[i+1].name)
                super_graph.add_edge(agent1_name, agent2_name)
            super_graph.add_edge(end_node_name, END)
        else:
            super_graph.add_edge(START, self.router_config.start_node)
            for edge in self.router_config.edges:
                super_graph.add_edge(edge[0], edge[1])
            super_graph.add_edge(self.router_config.end_node, END)

        super_graph = super_graph.compile()
        return FloRoutedTeam(self.flo_team.name, super_graph)
    
    class Builder():

        def __init__(self, session: FloSession, flo_team: FloTeam, config: RouterConfig) -> None:
            self.config = config
            self.session = session
            self.team = flo_team

        def build(self):
            return FloLinear(self.session, self.team, self.config)

