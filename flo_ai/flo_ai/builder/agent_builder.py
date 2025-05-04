from typing import List, Optional, Dict, Any
from flo_ai.models.agent import Agent
from flo_ai.models.base_agent import ReasoningPattern
from flo_ai.llm.base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool


class AgentBuilder:
    """
    A facade class that simplifies the creation and configuration of AI agents.
    """

    def __init__(self):
        self._name = 'AI Assistant'
        self._system_prompt = 'You are a helpful AI assistant.'
        self._llm: Optional[BaseLLM] = None
        self._tools: List[Tool] = []
        self._max_retries = 3
        self._reasoning_pattern = ReasoningPattern.DIRECT
        self._output_schema: Optional[Dict[str, Any]] = None

    def with_name(self, name: str) -> 'AgentBuilder':
        """Set the agent's name"""
        self._name = name
        return self

    def with_prompt(self, system_prompt: str) -> 'AgentBuilder':
        """Set the system prompt"""
        self._system_prompt = system_prompt
        return self

    def with_llm(self, llm: BaseLLM) -> 'AgentBuilder':
        """Configure the LLM to use

        Args:
            llm: An instance of a BaseLLM implementation
        """
        self._llm = llm
        return self

    def with_tools(self, tools: List[Tool]) -> 'AgentBuilder':
        """Add tools to the agent"""
        self._tools = tools
        return self

    def with_reasoning(self, pattern: ReasoningPattern) -> 'AgentBuilder':
        """Set the reasoning pattern"""
        self._reasoning_pattern = pattern
        return self

    def with_retries(self, max_retries: int) -> 'AgentBuilder':
        """Set maximum number of retries"""
        self._max_retries = max_retries
        return self

    def with_output_schema(self, schema: Dict[str, Any]) -> 'AgentBuilder':
        """Set output schema for structured responses"""
        self._output_schema = schema
        return self

    def build(self) -> Agent:
        """Build and return the configured agent"""
        if not self._llm:
            raise ValueError('LLM must be configured before building the agent')

        return Agent(
            name=self._name,
            system_prompt=self._system_prompt,
            llm=self._llm,
            tools=self._tools,
            max_retries=self._max_retries,
            reasoning_pattern=self._reasoning_pattern,
            output_schema=self._output_schema,
        )
