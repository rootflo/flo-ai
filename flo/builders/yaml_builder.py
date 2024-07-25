from flo.models.flo_team import FloTeamBuilder
from flo.models.flo_agent import FloAgentBuilder, FloAgent
from langchain_core.language_models import BaseLanguageModel
from flo.models.flo_supervisor import FloSupervisorBuilder, FloSupervisor
from flo.yaml.flo_team_builder import (FloSupervisedTeamConfig, TeamConfig, ToolConfig,
                                        AgentConfig, FloAgentConfig)
from flo.models.flo_executable import ExecutableFlo
from flo.models.flo_planner import FloPlannerBuilder
from flo.state.flo_session import FloSession
from typing import Union

def build_supervised_team(
        session: FloSession,
        flo_config: Union[FloSupervisedTeamConfig, FloAgentConfig]) -> ExecutableFlo:
    if isinstance(flo_config, FloSupervisedTeamConfig):
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
        # TODO supervisor is made nevertheless
        supervisor_name = team.supervisor.name if team.supervisor is not None else "supervisor"
        supervisor_agent: FloSupervisor = FloSupervisorBuilder(session, supervisor_name, agents).build()
        flo_team = FloTeamBuilder(
            session=session,
            name=team.name,
            supervisor=supervisor_agent
        ).build()
        if team.planner is not None:
            return FloPlannerBuilder(session, team.planner.name, flo_team).build()
    else:
        flo_teams = []
        for subteam in team.subteams:
            flo_subteam = parse_and_build_subteams(session, subteam, tool_map)
            flo_teams.append(flo_subteam)
        supervisor_name = team.supervisor.name if team.supervisor is not None else "supervisor"
        sub_team_supervisor_agent: FloSupervisor = FloSupervisorBuilder(session, supervisor_name, flo_teams).build()
        flo_team = FloTeamBuilder(
            session=session,
            name=team.name,
            supervisor=sub_team_supervisor_agent
        ).build()
    return flo_team
        
def create_agent(session: FloSession, agent: AgentConfig, tool_map) -> FloAgent:
    tools = [tool_map[tool.name] for tool in agent.tools]
    flo_agent: FloAgent = FloAgentBuilder(
        session,
        agent.name, 
        agent.prompt,
        tools
    ).build()
    return flo_agent

