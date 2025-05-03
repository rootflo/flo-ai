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

        # Add function calling context if needed
        if functions:
            function_desc = (
                'Available functions:\n'
                + json.dumps(functions, indent=2)
                + '\nTo use a function, respond with JSON in the format:'
                + '\n{"function": "function_name", "arguments": {"arg1": "value1", ...}}'
            )
            if system_message:
                system_message = system_message + '\n\n' + function_desc
            else:
                system_message = function_desc

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=conversation,
                system=system_message,
                temperature=self.temperature,
            )

            return {'content': response.content[0].text}
        except Exception as e:
            raise Exception(f'Error in Claude API call: {str(e)}')

    async def get_function_call(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        content = response['content']
        try:
            # Try to parse function call from response
            if '{"function":' in content:
                start_idx = content.find('{"function":')
                end_idx = content.find('}', start_idx) + 1
                function_json = content[start_idx:end_idx]
                function_data = json.loads(function_json)
                return {
                    'name': function_data['function'],
                    'arguments': json.dumps(function_data['arguments']),
                }
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def get_message_content(self, response: Dict[str, Any]) -> str:
        return response['content']
