import uuid
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from flo_ai.common.flo_logger import FloLogger, get_logger
from flo_ai.common.flo_callback_handler import FloCallbackHandler
from typing import Optional

class FloSession:
    def __init__(self, 
                 llm: BaseLanguageModel, 
                 loop_size: int = 2, 
                 max_loop: int = 3, 
                 log_level: str = "DEBUG",
                 custom_logger: Optional[FloLogger] = None,
                 custom_callback_handler: Optional[FloCallbackHandler] = None) -> None:
        self.session_id = str(uuid.uuid4())
        self.llm = llm
        self.tools = dict()
        self.counter = dict()
        self.navigation: list[str] = list()
        self.pattern_series = dict()
        self.loop_size: int = loop_size
        self.max_loop: int = max_loop
        self.logger = custom_logger or get_logger(f"FloSession-{self.session_id}", log_level)
        self.callback_handler = custom_callback_handler or FloCallbackHandler(f"FloCallback-{self.session_id}", log_level)
        self.logger.info(f"New FloSession created with ID: {self.session_id}")

    def register_tool(self, name: str, tool: BaseTool):
        self.tools[name] = tool
        self.logger.info(f"Tool '{name}' registered for session {self.session_id}")
        return self

    def append(self, node: str) -> int:
        self.logger.debug(f"Appending node: {node}")
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
        self.logger.debug(f"Checking if node {node} is looping")
        patterns = self.pattern_series[node] if node in self.pattern_series else []
        if len(patterns) < self.max_loop:
            return False
        return patterns[-(self.max_loop):] == [patterns[-1]] * self.max_loop

    def stringify(self):
        return str(self.counter)