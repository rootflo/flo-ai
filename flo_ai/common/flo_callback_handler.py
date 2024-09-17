from typing import Any, Dict, List, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from flo_ai.common.flo_logger import get_logger

class FloCallbackHandler(BaseCallbackHandler):
    def __init__(self, logger_name: str = "FloCallback", log_level: str = "INFO"):
        self.logger = get_logger(logger_name, log_level)

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        self.logger.info(f"onLLMStart: {prompts}")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.logger.debug(f"onNewToken: {token}")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self.logger.info(f"onLLMEnd: {response.generations}")

    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        self.logger.error(f"onLLMError: {error}")

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        self.logger.info(f"onChainStart: {inputs}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        self.logger.info(f"onChainEnd: {outputs}")

    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        self.logger.error(f"onChainError: {error}")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        self.logger.info(f"onToolStart: {input_str}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        self.logger.info(f"onToolEnd: {output}")

    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        self.logger.error(f"onToolError: {error}")

    def on_text(self, text: str, **kwargs: Any) -> None:
        self.logger.info(f"onText: {text}")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        self.logger.info(f"onAgentAction: {action.tool} - {action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        self.logger.info(f"onAgentFinish: {finish.return_values}")