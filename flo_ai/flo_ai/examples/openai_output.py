import asyncio
from textwrap import dedent
from pydantic import BaseModel
from flo_ai.llm.openai_llm import OpenAILLM
from flo_ai.llm.claude_llm import ClaudeLLM


# Define the output schema using Pydantic
class Step(BaseModel):
    explanation: str
    output: str


class MathReasoning(BaseModel):
    steps: list[Step]
    final_answer: str


math_tutor_prompt = """
    You are a helpful math tutor. You will be provided with a math problem,
    and your goal will be to output a step by step solution, along with a final answer.
    For each step, just provide the output as an equation use the explanation field to detail the reasoning.
    
    Provide your response in JSON format following the specified schema.
"""


async def main():
    # Initialize LLMs
    openai_llm = OpenAILLM(model='gpt-4-turbo-preview')
    claude_llm = ClaudeLLM()

    # OpenAI example
    openai_response = await openai_llm.generate(
        messages=[
            {'role': 'system', 'content': dedent(math_tutor_prompt)},
            {'role': 'user', 'content': 'Solve 8x + 7 = -23'},
        ],
        output_schema={
            'name': 'math_reasoning',
            'schema': {
                'type': 'object',
                'properties': {
                    'steps': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'explanation': {'type': 'string'},
                                'output': {'type': 'string'},
                            },
                            'required': ['explanation', 'output'],
                            'additionalProperties': False,
                        },
                    },
                    'final_answer': {'type': 'string'},
                },
                'required': ['steps', 'final_answer'],
                'additionalProperties': False,
            },
        },
    )
    print('OpenAI Response:', openai_response)

    # Claude example
    claude_response = await claude_llm.generate(
        messages=[{'role': 'user', 'content': 'Solve 8x + 7 = -23'}],
        output_schema=MathReasoning.model_json_schema(),
    )
    print('Claude Response:', claude_response)


if __name__ == '__main__':
    asyncio.run(main())
