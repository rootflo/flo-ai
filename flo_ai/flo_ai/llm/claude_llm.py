from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic
import json
from .base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool


class ClaudeLLM(BaseLLM):
    def __init__(
        self,
        model: str = 'claude-3-opus-20240229',
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        max_tokens: int = 4096,
    ):
        super().__init__(model, temperature)
        self.client = AsyncAnthropic(api_key=api_key)
        self.max_tokens = max_tokens

    async def generate(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # Convert messages to Claude format
        system_message = next(
            (msg['content'] for msg in messages if msg['role'] == 'system'), None
        )

        conversation = []
        for msg in messages:
            if msg['role'] != 'system':
                conversation.append(
                    {
                        'role': 'assistant' if msg['role'] == 'assistant' else 'user',
                        'content': msg['content'],
                    }
                )

        try:
            kwargs = {
                'model': self.model,
                'max_tokens': self.max_tokens,
                'messages': conversation,
                'temperature': self.temperature,
            }

            if system_message:
                kwargs['system'] = system_message

            if functions:
                kwargs['tools'] = functions

            response = await self.client.messages.create(**kwargs)

            # Check if there's a tool call in the response
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                # Extract the actual parameters from the tool call
                tool_parameters = (
                    tool_call.parameters if hasattr(tool_call, 'parameters') else {}
                )

                return {
                    'content': response.content[0].text if response.content else '',
                    'function_call': {
                        'name': tool_call.name,  # Changed from tool.name
                        'arguments': json.dumps(
                            tool_parameters
                        ),  # Use actual parameters
                    },
                }
            elif hasattr(response, 'content') and response.content:
                # Handle regular text response
                if isinstance(response.content, list) and len(response.content) > 0:
                    return {'content': response.content[0].text}
                return {'content': str(response.content)}
            else:
                return {'content': ''}

        except Exception as e:
            raise Exception(f'Error in Claude API call: {str(e)}')

    async def get_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Extract function call from response if present"""
        if 'function_call' in response:
            return {
                'name': response['function_call']['name'],
                'arguments': response['function_call']['arguments'],
            }
        return None

    def get_message_content(self, response: Dict[str, Any]) -> str:
        """Extract message content from response"""
        if isinstance(response, dict):
            return response.get('content', '')
        return str(response)

    def format_tool_for_llm(self, tool: 'Tool') -> Dict[str, Any]:
        """Format a single tool for Claude's API"""
        return {
            'type': 'custom',
            'name': tool.name,
            'description': tool.description,
            'input_schema': {
                'type': 'object',
                'properties': {
                    name: {
                        'type': info.get('type', 'string'),
                        'description': info.get('description', ''),
                    }
                    for name, info in tool.parameters.items()
                },
                'required': [
                    name
                    for name, info in tool.parameters.items()
                    if info.get('required', True)
                ],
            },
        }

    def format_tools_for_llm(self, tools: List['Tool']) -> List[Dict[str, Any]]:
        """Format tools for Claude's API"""
        return [self.format_tool_for_llm(tool) for tool in tools]
