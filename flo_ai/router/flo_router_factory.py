from typing import Optional
from flo_ai.state.flo_session import FloSession
from flo_ai.router.flo_supervisor import FloSupervisor
from flo_ai.router.flo_llm_router import FloLLMRouter
from flo_ai.router.flo_linear import FloLinear
from flo_ai.yaml.config import TeamConfig
from flo_ai.models.flo_team import FloTeam
from flo_ai.router.flo_router import FloRouter

class FloRouterFactory:

    @staticmethod
    def create(session: FloSession, team_config: TeamConfig, flo_team: FloTeam) -> FloRouter:
        router_kind = team_config.router.kind
        router_model = FloRouterFactory.__resolve_model(session, team_config.router.model)
        if router_kind == 'supervisor':
            return FloSupervisor.Builder(session, team_config, flo_team, llm=router_model).build()
        elif router_kind == 'linear':
            return FloLinear.Builder(session, team_config, flo_team).build()
        elif router_kind == 'llm':
            return FloLLMRouter.Builder(session, team_config, flo_team, llm=router_model).build()
        else:
            raise Exception("Unknown router type")
        
    @staticmethod
    def __resolve_model(session: FloSession, model_name: Optional[str] = None):
        if model_name is None:
            return session.llm
        if model_name not in session.models:
            # TODO raise proper exception
            raise f"Model not found: {model_name}"
        return session.models[model_name]
