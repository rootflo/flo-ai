from typing import Any, Dict, List, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from flo_ai.common.flo_logger import get_logger
from flo_ai.callbacks.flo_callbacks import FloToolCallback, FloAgentCallback, FloRouterCallback

class FloLangchainLogger(BaseCallbackHandler):
    def __init__(self, session_id: str, 
                 tool_callbacks: List[FloToolCallback] = None,
                 agent_callbacks: List[FloAgentCallback] = None,
                 router_callbacks: List[FloRouterCallback] = None):
        self.session_id = session_id
        self.tool_callbacks = tool_callbacks or []
        self.agent_callbacks = agent_callbacks or []
        self.router_callbacks = router_callbacks or []

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        print(f"on_llm_start: {serialized}")
        model_name = serialized.get("kwargs", {}).get("model_name", "unknown")
        for callback in self.router_callbacks:
            try:
                callback.on_router_start(
                    name=self.session_id,
                    model_name=model_name,
                    input=prompts[0] if prompts else None,
                    **kwargs
                )
            except Exception as e:
                get_logger().error(f"Error in router start callback: {e}")
        
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        get_logger().debug(f'onNewToken: {token}', self)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        for callback in self.router_callbacks:
            try:
                callback.on_router_end(
                    name=self.session_id,
                    model_name = response.generations[0][0].generation_info["model_name"],
                    output=str(response),
                    **kwargs
                )
            except Exception as e:
                get_logger().error(f"Error in router end callback: {e}")

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        get_logger().debug(f'onLLMEnd: {error}', self)

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        try:
            chain_name = serialized.get("name", "unknown") if serialized else "unknown"
            if serialized and "AgentExecutor" in str(chain_name):
                for callback in self.agent_callbacks:
                    callback.on_agent_start(
                        name=chain_name,
                        model_name="unknown",
                        input=str(inputs),
                        **kwargs
                    )
        except Exception as e:
            get_logger().error(f"Error in chain start callback: {e}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        try:
            for callback in self.agent_callbacks:
                callback.on_agent_end(
                    name=self.session_id,
                    model_name="unknown",
                    output=str(outputs),
                    **kwargs
                )
        except Exception as e:
            get_logger().error(f"Error in chain end callback: {e}")

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        get_logger().debug(f'onChainError: {error}', self)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        try:
            tool_name = serialized.get("name", "unknown") if serialized else "unknown"
            for callback in self.tool_callbacks:
                callback.on_tool_start(
                    name=tool_name,
                    input=input_str,
                    **{k: v for k, v in kwargs.items() if k != 'name'}  
                )
        except Exception as e:
            get_logger().error(f"Error in tool start callback: {e}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        try:
            tool_name = kwargs.get("name", "unknown")
            for callback in self.tool_callbacks:
                callback.on_tool_end(
                    name=tool_name,
                    output=output,
                    **{k: v for k, v in kwargs.items() if k != 'name'}  
                )
        except Exception as e:
            get_logger().error(f"Error in tool end callback: {e}")

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        try:
            tool_name = kwargs.get("name", "unknown")
            for callback in self.tool_callbacks:
                callback.on_tool_error(
                    name=tool_name,
                    error=error,
                    **{k: v for k, v in kwargs.items() if k != 'name'}
                )
        except Exception as e:
            get_logger().error(f"Error in tool error callback: {e}")

    def on_text(self, text: str, **kwargs: Any) -> None:
        get_logger().debug(f'onText: {text}', self)

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        get_logger().debug(f'onAgentAction: {action.tool} - {action.tool_input}', self)

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        get_logger().debug(f'onAgentFinish: {finish.return_values}', self)