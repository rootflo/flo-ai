import asyncio
from typing import Any
from flo_ai.builder.agent_builder import AgentBuilder
from flo_ai.models.agent import Agent
from flo_ai.models.chat_message import ChatMessage
from flo_ai.llm.base_llm import ImageMessage
from flo_ai.llm.gemini_llm import Gemini
from flo_ai.models.document import DocumentMessage
from flo_ai.models.document import DocumentType


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
            ChatMessage(
                role='user', content='What is the formula for the area of a circle?'
            ),
            ChatMessage(
                role='assistant',
                content='The formula for the area of a circle is πr^2.',
            ),
            ChatMessage(
                role='user', content='What is the formula for the area of a rectangle?'
            ),
            ChatMessage(
                role='assistant',
                content='The formula for the area of a rectangle is length * width.',
            ),
            ChatMessage(
                role='user', content='What is the formula for the area of a triangle?'
            ),
            ChatMessage(
                role='user', content=ImageMessage(image_file_path=' Downloads/download.png',mime_type='image/png')
            ),
            ChatMessage(
                role='user', content='from where he got this badge?'
            ),
            ChatMessage(
                role='user', content=DocumentMessage(document_file_path='doc_path.pdf',document_type=DocumentType.PDF)
            ),
            ChatMessage(
                role='user', content='what is the name of the person in the document?'
            )
        ]
    )
    print(f'Response: {response}')


asyncio.run(main())
