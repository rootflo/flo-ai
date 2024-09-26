from flo_ai.models.flo_team import FloTeam
from flo_ai.yaml.config import (FloRoutedTeamConfig, TeamConfig, AgentConfig, FloAgentConfig)
from flo_ai.models.flo_executable import ExecutableFlo
from flo_ai.state.flo_session import FloSession
from flo_ai.router.flo_router_factory import FloRouterFactory
from flo_ai.factory.agent_factory import AgentFactory
from flo_ai.yaml.validators import raise_for_name_error, DuplicateStringError
from flo_ai.common.flo_logger import builder_logger

def build_supervised_team(session: FloSession) -> ExecutableFlo:
    name_set = set()
    flo_config = session.config
    if isinstance(flo_config, FloRoutedTeamConfig):
        team_config: TeamConfig = flo_config.team
        team = parse_and_build_subteams(session, team_config, name_set)
        return team
    elif isinstance(flo_config, FloAgentConfig):
        agent_config: AgentConfig = flo_config.agent
        validate_names(name_set, agent_config.name)
        agent = AgentFactory.create(session, agent_config)
        return agent
    
def validate_team(name_set: set, team_config: TeamConfig):
    validate_names(name_set, team_config.name)
    [validate_names(name_set, agent.name) for agent in team_config.agents]

def parse_and_build_subteams(session: FloSession, team_config: TeamConfig, name_set = set()) -> ExecutableFlo:
    flo_team = None
    validate_team(name_set, team_config)
    if team_config.agents:
        members = [AgentFactory.create(session, agent) for agent in team_config.agents]
        flo_team = FloTeam.Builder(team_config, members=members).build()
        router = FloRouterFactory.create(session, team_config, flo_team)
        flo_routed_team = router.build_routed_team()
    else:
        flo_teams = []
        for subteam in team_config.subteams:
            flo_subteam = parse_and_build_subteams(session, subteam, name_set)
            flo_teams.append(flo_subteam)
        flo_team = FloTeam.Builder(team_config, members=flo_teams).build()
        router = FloRouterFactory.create(session, team_config, flo_team)
        flo_routed_team = router.build_routed_team()
    return flo_routed_team

def validate_names(name_set: set, name):
    raise_for_name_error(name)
    if name in name_set:
        builder_logger.error(f"Duplicate name found: '{name}'")
        raise DuplicateStringError(f"The name '{name}' is already in the set.")
    name_set.add(name)