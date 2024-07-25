from pydantic import BaseModel
from typing import List
import yaml
import re
from typing import Optional
from flo.models.exception import FloValidationException


KIND_SUPERVISED_TEAM = "FloSupervisedTeam"
KIND_FLO_AGENT = "FloAgent"

yaml_kinds = [
  KIND_SUPERVISED_TEAM,
  KIND_FLO_AGENT
]

class KeyValueArgs(BaseModel):
    name: str
    value: str

class FilterArgs(BaseModel):
    name: str
    description: str
    type: str

class ToolConfig(BaseModel):
    name: str
    args: Optional[List[KeyValueArgs]] = None
    properties: Optional[List[KeyValueArgs]] = None
    filters: Optional[List[FilterArgs]] = None

class AgentConfig(BaseModel):
    name: str
    kind: Optional[str] = None
    prompt: str
    tools: List[ToolConfig] = []

class SupervisorConfig(BaseModel):
    name: str

class PlannerConfig(BaseModel):
    name: str

class TeamConfig(BaseModel):
    name: str
    agents: Optional[List[AgentConfig]] = None
    subteams: Optional[List['TeamConfig']] = None
    supervisor: Optional[SupervisorConfig] = None
    planner: Optional[PlannerConfig] = None

class FloSupervisedTeamConfig(BaseModel):
    apiVersion: str
    kind: str
    name: str
    team: TeamConfig

class FloAgentConfig(BaseModel):
    apiVersion: str
    kind: str
    name: str
    agent: AgentConfig

def to_supervised_team(yaml_str: str) -> FloSupervisedTeamConfig:
    parsed_data = yaml.safe_load(yaml_str)
    kind = parsed_data["kind"]
    if kind == KIND_SUPERVISED_TEAM:
        flo_supervised_team = FloSupervisedTeamConfig(**parsed_data)
        validate_sup_team_config(flo_supervised_team)
        return flo_supervised_team
    elif kind == KIND_FLO_AGENT:
        flo_agent = FloAgentConfig(**parsed_data)
        validate_sup_team_config(flo_agent)
        return flo_agent
    else:
        raise FloValidationException("Unknown kind: {}".format(kind))

def validate_sup_team_config(flo: FloSupervisedTeamConfig):
    if flo.kind == KIND_FLO_AGENT:
        return
    if flo.name is None or not is_valid_name(flo.name):
        raise FloValidationException("Invalid agent name while creating the flow, expected: [^[a-z][a-z0-9_-]*$]")
    
def is_valid_name(s: str) -> bool:
    pattern = r'^[a-z][a-z0-9_-]*$'
    return bool(re.match(pattern, s))