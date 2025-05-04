from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from .base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool


class OpenAILLM(BaseLLM):
    def __init__(
        self,
        model: str = 'gpt-3.5-turbo',
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ):
        super().__init__(model, temperature)
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        kwargs = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
        }
        if functions:
            kwargs['functions'] = functions

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message

    async def get_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if hasattr(response, 'function_call') and response.function_call:
            return {
                'name': response.function_call.name,
                'arguments': response.function_call.arguments,
            }
        return None

    def get_message_content(self, response: Dict[str, Any]) -> str:
        return response.content

    def format_tool_for_llm(self, tool: 'Tool') -> Dict[str, Any]:
        """Format a single tool for OpenAI's API"""
        return {
            'name': tool.name,
            'description': tool.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    name: {'type': info['type'], 'description': info['description']}
                    for name, info in tool.parameters.items()
                },
                'required': list(tool.parameters.keys()),
            },
        }

    def format_tools_for_llm(self, tools: List['Tool']) -> List[Dict[str, Any]]:
        """Format tools for OpenAI's API"""
        return [self.format_tool_for_llm(tool) for tool in tools]
