import functools
from langchain_core.messages import HumanMessage
from langgraph.graph.graph import CompiledGraph
from langgraph.graph import StateGraph, END
from langchain.agents import AgentExecutor

from flo_ai.models.flo_executable import ExecutableFlo
from flo_ai.models.flo_agent import FloAgent
from flo_ai.models.flo_supervisor import FloSupervisor
from flo_ai.constants.prompt_constants import FLO_FINISH
from flo_ai.state.flo_state import TeamFloAgentState
from flo_ai.state.flo_session import FloSession
from flo_ai.helpers.utils import randomize_name

class FloAgentNode:
    def __init__(self, 
                 agent_node: functools.partial, 
                 name: str) -> None:
        self.agent_node = agent_node
        self.name = name

def teamflo_agent_node(state: TeamFloAgentState, agent: AgentExecutor, name: str):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}

# The following functions interoperate between the top level graph state
# and the state of the research sub-graph
# this makes it so that the states of each graph don't get intermixed
def enter_chain(message: str, members: list[str]):
    results = {
        "messages": [HumanMessage(content=message)],
        "team_members": ", ".join(members),
    }
    return results

class FloTeam(ExecutableFlo):
    def __init__(self, name: str, graph: CompiledGraph) -> None:
        super().__init__(name, graph)

    def draw(self, xray=True):
        return self.graph.get_graph(xray=xray).draw_mermaid_png()

class FloTeamChain():
    def __init__(self, name: str, chain) -> None:
        self.chain = chain
        self.name = name

class FloTeamBuilder:
    def __init__(self, 
                 session: FloSession,
                 name: str,
                 supervisor: FloSupervisor) -> None:
        self.name = randomize_name(name)
        self.session = session
        self.flo_agents = supervisor.agents
        self.flo_supervisor: FloSupervisor = supervisor
        self.members = list(map(lambda x: x.name, self.flo_agents))

    def build_node(self, flo_agent: FloAgent):
        agent_func = functools.partial(teamflo_agent_node, agent=flo_agent.executor, name=flo_agent.name)
        return FloAgentNode(agent_func, flo_agent.name)
    

    def build(self):
        if self.flo_supervisor.is_agent_supervisor():
            return self.build_agent_supervisor_graph()
        else:
            return self.build_team_supervisor_graph()
        
    def router(self, state: TeamFloAgentState):
        next = state["next"]
        conditional_map = {k: k for k in self.members}
        conditional_map[FLO_FINISH] = END
        self.session.append(node=next)
        if self.session.is_looping(node=next):
            return conditional_map[FLO_FINISH]
        return conditional_map[next]


    def build_agent_supervisor_graph(self) -> FloTeam:
        flo_agent_nodes = [self.build_node(flo_agent) for flo_agent in self.flo_agents]
        workflow = StateGraph(TeamFloAgentState)
        for flo_agent_node in flo_agent_nodes:
            workflow.add_node(flo_agent_node.name, flo_agent_node.agent_node)
        workflow.add_node(self.flo_supervisor.name, self.flo_supervisor.executor)
        for member in self.members:
            workflow.add_edge(member, self.flo_supervisor.name)

        workflow.add_conditional_edges(self.flo_supervisor.name, self.router)

        workflow.set_entry_point(self.flo_supervisor.name)
        workflow_graph = workflow.compile()
        return FloTeam(self.name, workflow_graph)
    
    def build_chain_for_teams(self, flo_team: FloTeam):
        # TODO lets see if we can convert to members
        return FloTeamChain(flo_team.name, (
            functools.partial(enter_chain, members=flo_team.graph.nodes)
            | flo_team.graph
        ))
    
    def get_last_message(self, state: TeamFloAgentState, second = None) -> str:
        return state["messages"][-1].content


    def join_graph(self, response: dict):
        return {"messages": [response["messages"][-1]]}
    
    def build_team_supervisor_graph(self) -> FloTeam:
        flo_team_entry_chains = [self.build_chain_for_teams(flo_agent) for flo_agent in self.flo_agents]
        # Define the graph.
        super_graph = StateGraph(TeamFloAgentState)
        # First add the nodes, which will do the work
        for flo_team_chain in flo_team_entry_chains:
            super_graph.add_node(flo_team_chain.name, self.get_last_message | flo_team_chain.chain | self.join_graph)
        super_graph.add_node(self.flo_supervisor.name, self.flo_supervisor.executor)

        for member in self.members:
            super_graph.add_edge(member, self.flo_supervisor.name)

        super_graph.add_conditional_edges(self.flo_supervisor.name, self.router)

        super_graph.set_entry_point(self.flo_supervisor.name)
        super_graph = super_graph.compile()
        return FloTeam(self.name, super_graph)

