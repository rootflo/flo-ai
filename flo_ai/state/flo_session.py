import warnings
from typing import Union, Dict
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from flo_ai.common.flo_logger import get_logger
from flo_ai.common.flo_langchain_logger import FloLangchainLogger
from flo_ai.yaml.config import FloRoutedTeamConfig, FloAgentConfig
from flo_ai.helpers.utils import random_str

from typing import Optional


def _handle_agent_error(error) -> str:
    error_message = str(error)[:50]
    return f"""
            Following error happened while agent execution, please retry with the fix for the same:
            {error_message}
        """


class FloSession:
    def __init__(
        self,
        default_llm: BaseLanguageModel = None,
        loop_size: int = 2,
        max_loop: int = 3,
        llm: BaseLanguageModel = None,
        log_level: Optional[str] = None,
        callbacks: Optional[FloLangchainLogger] = None,
        on_agent_error=_handle_agent_error,
    ) -> None:
        if log_level:
            warnings.warn(
                '`log_level` is deprecated and will be removed in a future version. '
                'Please use `Flo.set_log_level()` instead.',
                DeprecationWarning,
                stacklevel=2,
            )

        self.session_id = str(random_str(16))
        self.llm = self.resolve_llm(default_llm, llm)
        self.tools = dict()
        self.models: Dict[str, BaseLanguageModel] = dict()
        self.tools: Dict[str, BaseTool] = dict()
        self.counter = dict()
        self.navigation: list[str] = list()
        self.pattern_series = dict()
        self.loop_size: int = loop_size
        self.max_loop: int = max_loop
        self.on_agent_error = on_agent_error

        self.config: Union[FloRoutedTeamConfig, FloAgentConfig] = None
        get_logger().info('New session created ...', self)
        self.langchain_logger = FloLangchainLogger(self.session_id)

    def resolve_llm(
        self, default_llm: BaseLanguageModel = None, llm: BaseLanguageModel = None
    ):
        if default_llm is not None:
            return default_llm
        if llm:
            warnings.warn(
                '`llm` is deprecated and will be removed in a future version. '
                'Please use `default_llm` instead.',
                DeprecationWarning,
                stacklevel=2,
            )
            return llm

    def register_tool(self, name: str, tool: BaseTool):
        self.tools[name] = tool
        get_logger().info(f"Tool '{name}' registered for session {self.session_id}")
        return self

    def register_model(self, name: str, model: BaseLanguageModel):
        self.models[name] = model
        get_logger().info(f"Model '{name}' registered for session {self.session_id}")
        return self

    def append(self, node: str) -> int:
        get_logger().debug(f'Appending node: {node}')
        self.counter[node] = self.counter.get(node, 0) + 1
        if node in self.navigation:
            last_known_index = (
                len(self.navigation) - 1 - self.navigation[::-1].index(node)
            )
            pattern_array = self.navigation[last_known_index : len(self.navigation)]
            if len(pattern_array) + 1 >= self.loop_size:
                pattern = '|'.join(pattern_array) + '|' + node
                if node in self.pattern_series:
                    self.pattern_series[node].append(pattern)
                else:
                    self.pattern_series[node] = [pattern]
        self.navigation.append(node)

    def is_looping(self, node) -> bool:
        get_logger().debug(f'Checking if node {node} is looping')
        patterns = self.pattern_series[node] if node in self.pattern_series else []
        if len(patterns) < self.max_loop:
            return False
        return patterns[-(self.max_loop) :] == [patterns[-1]] * self.max_loop

    def stringify(self):
        return str(self.counter)
