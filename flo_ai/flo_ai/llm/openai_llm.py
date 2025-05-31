from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from .base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool


class OpenAILLM(BaseLLM):
    def __init__(self, model='gpt-4-turbo-preview', **kwargs):
        super().__init__(model=model)
        self.client = AsyncOpenAI()
        self.model = model
        self.kwargs = kwargs

    async def generate(
        self, messages: list[dict], output_schema: dict = None, **kwargs
    ) -> Any:
        # Convert output_schema to OpenAI format if provided
        if output_schema:
            kwargs['response_format'] = {'type': 'json_object'}
            kwargs['functions'] = [
                {
                    'name': output_schema.get('name', 'default'),
                    'parameters': output_schema.get('schema', output_schema),
                }
            ]
            kwargs['function_call'] = {'name': output_schema.get('name', 'default')}

        # Prepare OpenAI API parameters
        openai_kwargs = {
            'model': self.model,
            'messages': messages,
            **kwargs,
            **self.kwargs,
        }

        # Make the API call
        response = await self.client.chat.completions.create(**openai_kwargs)
        message = response.choices[0].message

        # Return the full message object instead of just the content
        return message

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
        # Handle both string responses and message objects
        if isinstance(response, str):
            return response
        # Otherwise return content if available
        return response.content if hasattr(response, 'content') else str(response)

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
