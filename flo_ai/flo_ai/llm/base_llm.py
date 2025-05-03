from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLM(ABC):
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
    ):
        self.model = model
        self.temperature = temperature

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        pass

    @abstractmethod
    async def get_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract function call from response if present"""
        pass

    @abstractmethod
    def get_message_content(self, response: Dict[str, Any]) -> str:
        """Extract message content from response"""
        pass
