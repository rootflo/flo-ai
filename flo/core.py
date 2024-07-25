from flo.tools import yaml_tool_map
from flo.yaml.flo_team_builder import to_supervised_team
from langchain_core.language_models import BaseLanguageModel
from flo.builders.yaml_builder import build_supervised_team, FloSupervisedTeamConfig
from typing import (
    Any,
    Iterator,
    Union
)
from flo.state.flo_session import FloSession
from flo.models.flo_executable import ExecutableFlo

class Flo:

    def __init__(self,
                 session: FloSession,
                 config: FloSupervisedTeamConfig) -> None:
        self.config = config
        self.runnable: ExecutableFlo = build_supervised_team(session, config)

    def stream(self, query, config = None) -> Iterator[Union[dict[str, Any], Any]]:
        return self.runnable.stream(query, config)
    
    def invoke(self, query, config = None) -> Iterator[Union[dict[str, Any], Any]]:
        return self.runnable.invoke(query, config)
    
    @staticmethod
    def build_with_yaml(session: FloSession, yaml: str):
        return Flo(session, to_supervised_team(yaml))

    def draw(self, xray=True):
        return self.runnable.draw(xray)
    
    def draw_to_file(self, filename: str, xray=True):
        from PIL import Image as PILImage
        import io
        byte_image = self.runnable.draw(xray)
        with io.BytesIO(byte_image) as image_io:
            image = PILImage.open(image_io)
            image.save(filename)

        