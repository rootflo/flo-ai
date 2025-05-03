from flo_ai.models.base_agent import BaseAgent, AgentType, AgentError, aclient


class ConversationalAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = 'gpt-3.5-turbo',
        temperature: float = 0.7,
    ):
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            agent_type=AgentType.CONVERSATIONAL,
            model=model,
            temperature=temperature,
        )

    async def run(self, input_text: str) -> str:
        self.add_to_history('user', input_text)
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                messages = [
                    {'role': 'system', 'content': self.system_prompt}
                ] + self.conversation_history

                response = await aclient.chat.completions.create(
                    model=self.model, messages=messages, temperature=self.temperature
                )

                assistant_message = response.choices[0].message.content
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
