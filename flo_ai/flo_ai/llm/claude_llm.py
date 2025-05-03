from typing import Dict, Any, List, Optional
from anthropic import AsyncAnthropic
import json
from .base_llm import BaseLLM


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

        # Convert functions to Claude tools format if provided
        tools = None
        if functions:
            tools = [
                {
                    'name': func['name'],
                    'description': func.get('description', ''),
                    'input_schema': {
                        'type': 'object',
                        'properties': func['parameters'].get('properties', {}),
                        'required': func['parameters'].get('required', []),
                    },
                }
                for func in functions
            ]

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=conversation,
                system=system_message,
                temperature=self.temperature,
                tools=tools,
            )

            # Check if there's a tool call in the response
            if (
                hasattr(response.content[0], 'tool_calls')
                and response.content[0].tool_calls
            ):
                tool_call = response.content[0].tool_calls[0]
                return {
                    'content': '',  # Empty content since we're using a tool
                    'function_call': {
                        'name': tool_call.name,
                        'arguments': json.dumps(tool_call.arguments),
                    },
                }

            return {'content': response.content[0].text}

        except Exception as e:
            raise Exception(f'Error in Claude API call: {str(e)}')

    async def get_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if 'function_call' in response:
            return {
                'name': response['function_call']['name'],
                'arguments': json.dumps(response['function_call']['arguments']),
            }
        return None

    def get_message_content(self, response: Dict[str, Any]) -> str:
        return response['content']
