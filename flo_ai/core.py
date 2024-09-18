from flo_ai.yaml.flo_team_builder import to_supervised_team
from flo_ai.builders.yaml_builder import build_supervised_team, FloRoutedTeamConfig
from typing import (
    Any,
    Iterator,
    Union
)
from flo_ai.state.flo_session import FloSession
from flo_ai.models.flo_executable import ExecutableFlo
from flo_ai.common.flo_logger import common_logger, builder_logger, FloLogger

class Flo:

    def __init__(self,
                 session: FloSession,
                 config: FloRoutedTeamConfig,
                 log_level: str = "INFO") -> None:
        self.config = config
        self.session = session
        self.runnable: ExecutableFlo = build_supervised_team(session, config)

        FloLogger.set_log_level("COMMON", log_level)
        FloLogger.set_log_level("BUILDER", log_level)
        self.logger = common_logger
        self.langchain_logger = session.langchain_logger
        self.logger.info(f"Flo instance created for session {session.session_id}")

    def stream(self, query, config = None) -> Iterator[Union[dict[str, Any], Any]]:
        self.logger.info(f"Streaming query for session {self.session.session_id}: {query}")
        return self.runnable.stream(query, config)
    
    def invoke(self, query, config = None) -> Iterator[Union[dict[str, Any], Any]]:
        self.logger.info(f"Invoking query for session {self.session.session_id}: {query}")
        return self.runnable.invoke(query, config)
    
    @staticmethod
    def build(session: FloSession, yaml: str, log_level: str = "INFO"):
        FloLogger.set_log_level("BUILDER", log_level)
        builder_logger.info("Building Flo instance from YAML")
        return Flo(session, to_supervised_team(yaml), log_level)

    def draw(self, xray=True):
        return self.runnable.draw(xray)
    
    def draw_to_file(self, filename: str, xray=True):
        from PIL import Image as PILImage
        import io
        byte_image = self.runnable.draw(xray)
        with io.BytesIO(byte_image) as image_io:
            image = PILImage.open(image_io)
            image.save(filename)

        