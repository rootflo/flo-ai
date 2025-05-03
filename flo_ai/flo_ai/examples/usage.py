import asyncio
from flo_ai.models.conversational_agent import ConversationalAgent
from flo_ai.models.tool_agent import ToolAgent, Tool
from flo_ai.models.base_agent import AgentError


# Example of a simple conversational agent
async def test_conversational():
    agent = ConversationalAgent(
        name='Assistant',
        system_prompt='You are a helpful AI assistant.',
        model='gpt-4o',
    )

    response = await agent.run('What is the capital of France?')
    print(response)


# Example of a tool-using agent
async def test_tool_agent():
    # Define a simple tool
    async def get_weather(city: str) -> str:
        # This would normally call a weather API
        return f'The weather in {city} is sunny'

    weather_tool = Tool(
        name='get_weather',
        description='Get the weather for a city',
        function=get_weather,
        parameters={
            'city': {'type': 'string', 'description': 'The city to get weather for'}
        },
    )

    agent = ToolAgent(
        name='WeatherAssistant',
        system_prompt='You are a helpful weather assistant.',
        tools=[weather_tool],
        model='gpt-3.5-turbo',
    )

    response = await agent.run("What's the weather like in Paris?")
    print(response)


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

    agent = ToolAgent(
        name='WeatherAssistant',
        system_prompt='You are a helpful weather assistant.',
        tools=[weather_tool],
        model='gpt-3.5-turbo',
        max_retries=3,
    )

    try:
        # This will trigger error handling and retries
        response = await agent.run("What's the weather like in error?")
        print(response)
    except AgentError as e:
        print(f'Agent error: {str(e)}')
        if e.original_error:
            print(f'Original error: {str(e.original_error)}')


# Run the examples
if __name__ == '__main__':
    asyncio.run(test_conversational())
    asyncio.run(test_tool_agent())
    asyncio.run(test_error_handling())
