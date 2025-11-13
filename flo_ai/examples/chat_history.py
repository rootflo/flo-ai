import asyncio
from typing import Any
from flo_ai.builder.agent_builder import AgentBuilder
from flo_ai.llm import OpenAI, Gemini
from flo_ai.models.agent import Agent
from flo_ai.models import   AssistantMessage, UserMessage, TextMessageContent, ImageMessageContent

async def main() -> None:
    # Create a simple conversational agent
    agent: Agent = (
        AgentBuilder()
        .with_name('Math Tutor')
        .with_prompt('You are a helpful math tutor.')
        .with_llm(Gemini(model='gemini-2.5-flash'))
        .build()
    )

    response: Any = await agent.run(
        [   
            UserMessage(
                TextMessageContent(type='text', text='What is the formula for the area of a circle?'),
            ),
            AssistantMessage(
               TextMessageContent(type='text', text='The formula for the area of a circle is πr^2.'),
            ),
            UserMessage(
                TextMessageContent(type='text', text='What is the formula for the area of a rectangle?')
            ),
            AssistantMessage(
               TextMessageContent(type='text', text='The formula for the area of a rectangle is length * width.'),
            ),
        
           UserMessage(
                TextMessageContent(type='text', text=f'What is the area of a rectable of length <length> and breadth <breadth>'),
            ),
        ],
        variables={
            "length":10,
            "breadth":70
        },
    )
    print(f'Response: {response}')
asyncio.run(main())
