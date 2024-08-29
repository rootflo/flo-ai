from flo_ai.models.flo_team import FloTeamBuilder
from flo_ai.models.flo_agent import FloAgentBuilder, FloAgent
from flo_ai.yaml.flo_team_builder import (FloRoutedTeamConfig, TeamConfig,
                                        AgentConfig, FloAgentConfig)
from flo_ai.models.flo_executable import ExecutableFlo
from flo_ai.models.flo_planner import FloPlannerBuilder
from flo_ai.state.flo_session import FloSession
from flo_ai.router.flo_router import FloRouterBuilder
from typing import Union

def build_supervised_team(
        session: FloSession,
        flo_config: Union[FloRoutedTeamConfig, FloAgentConfig]) -> ExecutableFlo:
    if isinstance(flo_config, FloRoutedTeamConfig):
        team_config: TeamConfig = flo_config.team
        team = parse_and_build_subteams(session, team_config, session.tools)    
        return team
    elif isinstance(flo_config, FloAgentConfig):
        agent_config: AgentConfig = flo_config.agent
        agent = create_agent(session, agent_config, session.tools)
        return agent

def parse_and_build_subteams(
        session: FloSession,
        team: TeamConfig,
        tool_map) -> ExecutableFlo:
    flo_team = None
    if team.agents:
        agents = []
        for agent in team.agents:
            flo_agent: FloAgent = create_agent(session, agent, tool_map)
            agents.append(flo_agent)
        router = FloRouterBuilder(session, team, agents).build()
        flo_team = FloTeamBuilder(
            session=session,
            name=team.name,
            router=router
        ).build()
        if team.planner is not None:
            return FloPlannerBuilder(session, team.planner.name, flo_team).build()
    else:
        flo_teams = []
        for subteam in team.subteams:
            flo_subteam = parse_and_build_subteams(session, subteam, tool_map)
            flo_teams.append(flo_subteam)
        router = FloRouterBuilder(session, team, flo_teams).build()
        flo_team = FloTeamBuilder(
            session=session,
            name=team.name,
            router=router
        ).build()
    return flo_team
        
def create_agent(session: FloSession, agent: AgentConfig, tool_map) -> FloAgent:
    tools = [tool_map[tool.name] for tool in agent.tools]
    flo_agent: FloAgent = FloAgentBuilder(
        session,
        agent.name, 
        agent.job,
        tools
    ).build()
    return flo_agent

