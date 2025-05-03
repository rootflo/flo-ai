import asyncio
import os
from flo_ai.models.conversational_agent import ConversationalAgent
from flo_ai.models.tool_agent import ToolAgent, Tool
from flo_ai.models.base_agent import AgentError
from flo_ai.llm.claude_llm import ClaudeLLM


async def test_claude_conversational():
    # Initialize Claude LLM
    claude_llm = ClaudeLLM(
        model='claude-3-opus-20240229',
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY'),
    )

    # Create conversational agent with Claude
    agent = ConversationalAgent(
        name='ClaudeAssistant',
        system_prompt='You are a helpful AI assistant powered by Claude.',
        llm=claude_llm,
    )

    try:
        response = await agent.run(
            'What are the main differences between Python and JavaScript?'
        )
        print('\nConversational Agent Response:')
        print(response)
    except AgentError as e:
        print(f'Error: {str(e)}')


async def test_claude_tool_agent():
    # Example weather tool
    async def get_weather(city: str, country: str = None) -> str:
        # This would normally call a weather API
        return f'The weather in {city}{", " + country if country else ""} is sunny and warm.'

    weather_tool = Tool(
        name='get_weather',
        description='Get the current weather for a city',
        function=get_weather,
        parameters={
            'city': {'type': 'string', 'description': 'The city to get weather for'},
            'country': {
                'type': 'string',
                'description': 'The country of the city (optional)',
                'required': False,
            },
        },
    )

    # Initialize Claude LLM
    claude_llm = ClaudeLLM(
        model='claude-3-opus-20240229',
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY'),
    )

    # Create tool agent with Claude
    agent = ToolAgent(
        name='ClaudeWeatherAssistant',
        system_prompt='You are a helpful weather assistant. Use the weather tool to provide weather information.',
        tools=[weather_tool],
        llm=claude_llm,
    )

    try:
        # Test with different queries
        queries = [
            "What's the weather like in Tokyo?",
            'Tell me the weather in Paris, France',
            "How's the weather in New York City, USA?",
        ]

        for query in queries:
            print(f'\nQuery: {query}')
            response = await agent.run(query)
            print(f'Response: {response}')

    except AgentError as e:
        print(f'Error: {str(e)}')
        if e.original_error:
            print(f'Original error: {str(e.original_error)}')


async def test_error_handling():
    # Example of a tool that might fail
    async def flaky_weather(city: str) -> str:
        if city.lower() == 'error':
            raise ValueError('API temporarily unavailable')
        return f'The weather in {city} is sunny'

    weather_tool = Tool(
        name='get_weather',
        description='Get the weather for a city',
        function=flaky_weather,
        parameters={
            'city': {'type': 'string', 'description': 'The city to get weather for'}
        },
    )

    claude_llm = ClaudeLLM(
        model='claude-3-opus-20240229',
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY'),
    )

    agent = ToolAgent(
        name='ClaudeWeatherAssistant',
        system_prompt='You are a helpful weather assistant.',
        tools=[weather_tool],
        llm=claude_llm,
        max_retries=3,
    )

    try:
        # This will trigger error handling and retries
        response = await agent.run("What's the weather like in error?")
        print('\nResponse:', response)
    except AgentError as e:
        print('\nAgent error:', str(e))
        if e.original_error:
            print('Original error:', str(e.original_error))


async def main():
    print('\n=== Testing Claude Conversational Agent ===')
    await test_claude_conversational()

    print('\n=== Testing Claude Tool Agent ===')
    await test_claude_tool_agent()

    print('\n=== Testing Error Handling ===')
    await test_error_handling()


if __name__ == '__main__':
    asyncio.run(main())
