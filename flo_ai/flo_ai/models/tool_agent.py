from typing import Dict, Any, List, Optional
from flo_ai.models.base_agent import BaseAgent, AgentType, ReasoningPattern
from flo_ai.llm.base_llm import BaseLLM
from flo_ai.tool.base_tool import Tool, ToolExecutionError
from flo_ai.models.agent_error import AgentError
import json


class ToolAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: BaseLLM,
        tools: Optional[List[Tool]] = None,
        max_retries: int = 3,
        reasoning_pattern: ReasoningPattern = ReasoningPattern.DIRECT,
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

                response = await self.llm.generate(messages)
                assistant_message = self.llm.get_message_content(response)
                self.add_to_history('assistant', assistant_message)
                return assistant_message

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

                # Use LLM's tool formatting method
                formatted_tools = self.llm.format_tools_for_llm(self.tools)
                response = await self.llm.generate(
                    messages,
                    functions=formatted_tools,
                )
                print(f'Response: {response}')
                # Handle ReACT pattern
                if self.reasoning_pattern == ReasoningPattern.REACT:
                    function_call = await self._process_react_response(response)
                else:
                    function_call = await self.llm.get_function_call(response)

                if function_call:
                    try:
                        function_name = function_call['name']
                        function_args = json.loads(function_call['arguments'])

                        tool = self.tools_dict[function_name]
                        function_response = await tool.execute(**function_args)
                        print(f'Function response: {function_response}')

                        # Add thought process to history if present
                        thought_content = self.llm.get_message_content(response)
                        if thought_content:
                            self.add_to_history('assistant', thought_content)

                        # Add function call to history
                        self.add_to_history(
                            'function',
                            f'Tool response: {str(function_response)}',
                            name=function_name,
                        )

                        # Create a new message list for the final response
                        final_messages = [
                            {
                                'role': 'system',
                                'content': 'You are a helpful assistant. Provide a natural response based on the tool results.',
                            },
                            {
                                'role': 'user',
                                'content': f'Here is the {tool.name} information: {str(function_response)}. Please provide a natural response based on this {tool.name} data.',
                            },
                        ]

                        final_response = await self.llm.generate(final_messages)
                        assistant_message = self.llm.get_message_content(final_response)
                        self.add_to_history('assistant', assistant_message)
                        return assistant_message

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

                else:
                    assistant_message = self.llm.get_message_content(response)
                    self.add_to_history('assistant', assistant_message)
                    return assistant_message

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
        content = self.llm.get_message_content(response)

        # Add thought to history
        if 'Thought:' in content:
            thought = content.split('Action:')[0].strip()
            print(f'Thought: {thought}')
            self.add_to_history('thought', thought)

        # Extract action if present
        if 'Action:' in content:
            action = content.split('Action:')[1]
            if 'Observation:' in action:
                action = action.split('Observation:')[0]
            print(f'Action: {action}')
            action = action.strip()

            # Parse action into function call format
            try:
                action_parts = action.split('(', 1)
                function_name = action_parts[0].strip()
                args_str = action_parts[1].rstrip(')')
                function_args = json.loads('{' + args_str + '}')

                return {'name': function_name, 'arguments': json.dumps(function_args)}
            except Exception as e:
                self.add_to_history('system', f'Failed to parse action: {str(e)}')
                return None

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
