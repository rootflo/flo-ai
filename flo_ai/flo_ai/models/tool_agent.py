from typing import Dict, Any, List, Callable
from flo_ai.models.base_agent import BaseAgent, AgentType, AgentError
from flo_ai.llm.base_llm import BaseLLM
import json


class ToolExecutionError(AgentError):
    """Error during tool execution"""

    pass


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Dict[str, Any]],
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters

    def to_openai_function(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'parameters': {
                'type': 'object',
                'properties': self.parameters,
                'required': list(self.parameters.keys()),
            },
        }

    async def execute(self, **kwargs) -> Any:
        """Execute the tool with error handling"""
        try:
            return await self.function(**kwargs)
        except Exception as e:
            raise ToolExecutionError(
                f'Error executing tool {self.name}: {str(e)}', original_error=e
            )


class ToolAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List[Tool],
        llm: BaseLLM,
        max_retries: int = 3,
    ):
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            agent_type=AgentType.TOOL_USING,
            llm=llm,
            max_retries=max_retries,
        )
        self.tools = tools
        self.tools_dict = {tool.name: tool for tool in tools}

    async def run(self, input_text: str) -> str:
        self.add_to_history('user', input_text)
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                messages = [
                    {'role': 'system', 'content': self.system_prompt}
                ] + self.conversation_history

                response = await self.llm.generate(
                    messages,
                    functions=[tool.to_openai_function() for tool in self.tools],
                )

                function_call = await self.llm.get_function_call(response)

                if function_call:
                    try:
                        function_name = function_call['name']
                        function_args = json.loads(function_call['arguments'])

                        tool = self.tools_dict[function_name]
                        function_response = await tool.execute(**function_args)

                        self.add_to_history(
                            'assistant',
                            f'Called {function_name} with args {function_args}',
                        )
                        self.add_to_history('function', str(function_response))

                        final_response = await self.llm.generate(
                            messages
                            + [{'role': 'assistant', 'content': str(function_response)}]
                        )

                        assistant_message = self.llm.get_message_content(final_response)
                        self.add_to_history('assistant', assistant_message)
                        return assistant_message

                    except (json.JSONDecodeError, KeyError, ToolExecutionError) as e:
                        context = {
                            'input_text': input_text,
                            'function_call': function_call,
                            'attempt': retry_count,
                        }
                        should_retry, analysis = await self.handle_error(e, context)
                        if should_retry and retry_count < self.max_retries:
                            retry_count += 1
                            self.add_to_history(
                                'system', f'Tool execution error: {analysis}'
                            )
                            continue
                        raise AgentError(
                            f'Tool execution failed: {analysis}', original_error=e
                        )

                else:
                    assistant_message = self.llm.get_message_content(response)
                    self.add_to_history('assistant', assistant_message)
                    return assistant_message

            except Exception as e:
                retry_count += 1
                context = {
                    'input_text': input_text,
                    'conversation_history': self.conversation_history,
                    'attempt': retry_count,
                }

                should_retry, analysis = await self.handle_error(e, context)

                if should_retry and retry_count < self.max_retries:
                    self.add_to_history(
                        'system', f'Error occurred. Analysis: {analysis}'
                    )
                    continue
                else:
                    raise AgentError(
                        f'Failed after {retry_count} attempts. Last error: {analysis}',
                        original_error=e,
                    )
