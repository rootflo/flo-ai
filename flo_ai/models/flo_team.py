from flo_ai.models.flo_member import FloMember
from flo_ai.helpers.utils import randomize_name
from flo_ai.yaml.config import TeamConfig

class FloTeam():
    def __init__(self, team_config: TeamConfig, members: list[FloMember], reflection_agents: list[FloMember] = None) -> None:
        self.name = randomize_name(team_config.name)
        self.config = team_config
        self.members = members
        self.reflection_agents = reflection_agents

    class Builder:
        def __init__(self, team_config: TeamConfig, members: list[FloMember], reflection_agents: list[FloMember] = None) -> None:
            self.team_config = team_config
            self.members = members
            self.reflection_agents = reflection_agents
            self.member_names= list(map(lambda x: x.name, self.members))
            
        def build(self):
            return FloTeam(
                team_config=self.team_config, 
                members=self.members,
                reflection_agents=self.reflection_agents
            )