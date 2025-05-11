from typing import Dict, Any, List, Optional
from flo_ai.models.base_agent import BaseAgent, AgentType, ReasoningPattern
from flo_ai.llm.base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool, ToolExecutionError
from flo_ai.models.agent_error import AgentError
import json


class Agent(BaseAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: BaseLLM,
        tools: Optional[List[Tool]] = None,
        max_retries: int = 3,
        reasoning_pattern: ReasoningPattern = ReasoningPattern.DIRECT,
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        # Determine agent type based on tools
        agent_type = AgentType.TOOL_USING if tools else AgentType.CONVERSATIONAL

        super().__init__(
            name=name,
            system_prompt=system_prompt,
            agent_type=agent_type,
            llm=llm,
            max_retries=max_retries,
        )
        self.tools = tools or []
        self.tools_dict = {tool.name: tool for tool in self.tools}
        self.reasoning_pattern = reasoning_pattern
        self.output_schema = output_schema

    async def run(self, input_text: str) -> str:
        self.add_to_history('user', input_text)
        retry_count = 0

        # If no tools, act as conversational agent
        if not self.tools:
            return await self._run_conversational(retry_count)

        # Otherwise, run as tool agent
        return await self._run_with_tools(retry_count)

    async def _run_conversational(self, retry_count: int) -> str:
        """Run as a conversational agent when no tools are provided"""
        while retry_count < self.max_retries:
            try:
                messages = [
                    {'role': 'system', 'content': self.system_prompt}
                ] + self.conversation_history

                print('Sending messages to LLM:', messages)  # Debug print
                print('Output schema:', self.output_schema)  # Debug print

                response = await self.llm.generate(
                    messages, output_schema=self.output_schema
                )
                print('Raw LLM Response:', response)  # Debug print

                assistant_message = self.llm.get_message_content(response)
                print('Extracted message:', assistant_message)  # Debug print

                if assistant_message:
                    self.add_to_history('assistant', assistant_message)
                    return assistant_message
                else:
                    print(
                        'Warning: No message content found in response'
                    )  # Debug print
                    return None

            except Exception as e:
                retry_count += 1
                context = {
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

    async def _run_with_tools(self, retry_count: int = 0) -> str:
        """Run as a tool-using agent when tools are provided"""
        while retry_count < self.max_retries:
            try:
                messages = [
                    {
                        'role': 'system',
                        'content': self._get_react_prompt()
                        if self.reasoning_pattern == ReasoningPattern.REACT
                        else self.system_prompt,
                    }
                ] + self.conversation_history

                # Keep executing tools until we get a final answer
                max_tool_calls = 5  # Limit the number of tool calls per query
                tool_call_count = 0

                while tool_call_count < max_tool_calls:
                    formatted_tools = self.llm.format_tools_for_llm(self.tools)
                    response = await self.llm.generate(
                        messages,
                        functions=formatted_tools,
                        output_schema=self.output_schema,
                    )

                    # Handle ReACT pattern
                    if self.reasoning_pattern == ReasoningPattern.REACT:
                        function_call = await self._process_react_response(response)
                    else:
                        function_call = await self.llm.get_function_call(response)

                    # If no function call, we have our final answer
                    if not function_call:
                        assistant_message = self.llm.get_message_content(response)
                        if assistant_message:
                            self.add_to_history('assistant', assistant_message)
                            return assistant_message
                        break

                    # Execute the tool
                    try:
                        function_name = function_call['name']
                        function_args = json.loads(function_call['arguments'])

                        tool = self.tools_dict[function_name]
                        function_response = await tool.execute(**function_args)
                        tool_call_count += 1

                        # Add function call to history
                        self.add_to_history(
                            'function',
                            f'Tool response: {str(function_response)}',
                            name=function_name,
                        )

                        # Add the function response to messages for context
                        messages.append(
                            {
                                'role': 'function',
                                'name': function_name,
                                'content': str(function_response),
                            }
                        )

                        # Add a prompt to continue the reasoning
                        messages.append(
                            {
                                'role': 'user',
                                'content': 'Continue with your reasoning based on this result. What should be done next?',
                            }
                        )

                    except (json.JSONDecodeError, KeyError, ToolExecutionError) as e:
                        retry_count += 1
                        context = {
                            'function_call': function_call,
                            'attempt': retry_count,
                        }
                        should_retry, analysis = await self.handle_error(e, context)
                        if should_retry and retry_count < self.max_retries:
                            self.add_to_history(
                                'system', f'Tool execution error: {analysis}'
                            )
                            continue
                        raise AgentError(
                            f'Tool execution failed: {analysis}', original_error=e
                        )

                # Generate final response if we've hit the tool call limit or exited the loop
                final_response = await self.llm.generate(
                    messages
                    + [
                        {
                            'role': 'system',
                            'content': 'Please provide a final answer based on all the tool results above.',
                        }
                    ],
                    output_schema=self.output_schema,
                )

                assistant_message = self.llm.get_message_content(final_response)
                if assistant_message:
                    self.add_to_history('assistant', assistant_message)
                    return assistant_message

                return f'The final result based on the tool executions is: {function_response}'

            except Exception as e:
                retry_count += 1
                context = {
                    'conversation_history': self.conversation_history,
                    'attempt': retry_count,
                }

                should_retry, analysis = await self.handle_error(e, context)
                if should_retry and retry_count < self.max_retries:
                    self.add_to_history(
                        'system', f'Error occurred. Analysis: {analysis}'
                    )
                    continue

                raise AgentError(
                    f'Failed after {retry_count} attempts. Last error: {analysis}',
                    original_error=e,
                )

        raise AgentError(f'Failed after maximum {self.max_retries} attempts.')

    async def _process_react_response(
        self, response: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process response in ReACT format and return function call if action is needed"""

        # Get the message content first (contains the thought process)
        content = self.llm.get_message_content(response)
        if content:
            self.add_to_history('assistant', content)

        # Handle both OpenAI and Claude response formats
        function_call = None
        if hasattr(response, 'function_call'):  # OpenAI format
            function_call = response.function_call
        elif (
            isinstance(response, dict) and 'function_call' in response
        ):  # Claude format
            function_call = response['function_call']

        if function_call:
            return {
                'name': function_call.name
                if hasattr(function_call, 'name')
                else function_call['name'],
                'arguments': function_call.arguments
                if hasattr(function_call, 'arguments')
                else function_call['arguments'],
            }

        return None

    def _get_react_prompt(self) -> str:
        """Get system prompt modified for ReACT pattern"""
        tools_desc = '\n'.join(
            [f'- {tool.name}: {tool.description}' for tool in self.tools]
        )
        react_prompt = f"""{self.system_prompt}
            When solving tasks, follow this format:

            Thought: Analyze the situation and think about what to do
            Action: Use available tools in the format: tool_name(param1: "value1", param2: "value2")
            Observation: The result of the action
            ... (repeat Thought/Action/Observation if needed)

            Available tools:
            {tools_desc}

            Remember to:
            1. Think carefully about what needs to be done
            2. Use tools when needed
            3. Make observations about tool results
            4. Conclude with a final answer when the task is complete"""

        return react_prompt
