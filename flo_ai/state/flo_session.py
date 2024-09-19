from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from flo_ai.yaml.config import to_supervised_team
from typing import Union
from flo_ai.yaml.config import (FloRoutedTeamConfig, FloAgentConfig)
class FloSession:
    def __init__(self, llm: BaseLanguageModel, yaml_config: str | None, loop_size: int = 2, max_loop: int = 3) -> None:
        self.llm = llm
        self.tools = dict()
        self.counter = dict()
        self.navigation: list[str] = list()
        self.pattern_series = dict()
        self.loop_size: int = loop_size
        self.max_loop: int = max_loop
        self.config: Union[FloRoutedTeamConfig, FloAgentConfig] = to_supervised_team(yaml_str=yaml_config) if isinstance(yaml_config, str) else None

    def register_tool(self, name: str, tool: BaseTool):
        self.tools[name] = tool
        return self

    def append(self, node: str) -> int:
        self.counter[node] = self.counter.get(node, 0) + 1
        if node in self.navigation:
            last_known_index = len(self.navigation) - 1 - self.navigation[::-1].index(node)
            pattern_array = self.navigation[last_known_index: len(self.navigation)]
            if len(pattern_array) + 1 >= self.loop_size:
                pattern = "|".join(pattern_array) + "|" + node
                if node in self.pattern_series:
                    self.pattern_series[node].append(pattern)
                else:
                    self.pattern_series[node] = [pattern]
        self.navigation.append(node)

    def is_looping(self, node) -> bool:
        patterns = self.pattern_series[node] if node in self.pattern_series else []
        if len(patterns) < self.max_loop:
            return False
        return patterns[-(self.max_loop):] == [patterns[-1]] * self.max_loop

    def stringify(self):
        return str(self.counter)