#!/usr/bin/env python3
"""
Example usage of BigQuery tools with flo_ai framework.

This script demonstrates how to:
1. Set up BigQuery connection using environment variables
2. Use the BigQuery tools with an AI agent
3. Execute various database operations
"""

import asyncio
import os
from flo_ai.builder.agent_builder import AgentBuilder
from flo_ai.models.base_agent import ReasoningPattern
from flo_ai.llm.openai_llm import OpenAI
from flo_ai_tools.tools.bigquery_tools import (
    execute_bigquery_query,
    get_bigquery_table_schema,
    list_bigquery_datasets,
    list_bigquery_tables,
    get_bigquery_table_info,
)


def setup_bigquery_environment():
    """Setup BigQuery environment variables for demonstration."""

    # Set default values for demonstration (in production, these would be set in your environment)
    if not os.getenv('BIGQUERY_PROJECT_ID'):
        os.environ['BIGQUERY_PROJECT_ID'] = 'your-project-id'
    if not os.getenv('BIGQUERY_LOCATION'):
        os.environ['BIGQUERY_LOCATION'] = 'US'
    if not os.getenv('BIGQUERY_USE_DEFAULT_CREDENTIALS'):
        os.environ['BIGQUERY_USE_DEFAULT_CREDENTIALS'] = 'true'

    print('BigQuery environment configured:')
    print(f"  Project ID: {os.getenv('BIGQUERY_PROJECT_ID')}")
    print(f"  Location: {os.getenv('BIGQUERY_LOCATION')}")
    print(f"  Use Default Credentials: {os.getenv('BIGQUERY_USE_DEFAULT_CREDENTIALS')}")

    # Note: For service account authentication, you would set:
    # export BIGQUERY_CREDENTIALS_PATH=/path/to/service-account.json
    # export BIGQUERY_USE_DEFAULT_CREDENTIALS=false


async def demonstrate_ai_agent_with_tools():
    """Demonstrate using BigQuery tools with an AI agent."""

    print('\n=== Demonstrating AI Agent with BigQuery Tools ===\n')

    # Create an LLM instance (you'll need to set your API key)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('⚠️  OPENAI_API_KEY not set. Skipping AI agent demonstration.')
        return

    llm = OpenAI(model='gpt-4o-mini', api_key=api_key)

    # Create an agent with BigQuery tools
    agent = (
        AgentBuilder()
        .with_name('BigQuery Data Analyst')
        .with_prompt("""You are a data analyst with access to BigQuery. 
                        You can execute SQL queries, explore table schemas, and analyze data.
                        Always use the appropriate tools to answer questions about the database.
                        Be helpful and provide clear explanations of your findings.
                        When working with BigQuery, remember that tables are organized as project.dataset.table.""")
        .with_llm(llm)
        .with_tools(
            [
                execute_bigquery_query.tool,
                get_bigquery_table_schema.tool,
                list_bigquery_datasets.tool,
                list_bigquery_tables.tool,
                get_bigquery_table_info.tool,
            ]
        )
        .with_reasoning(ReasoningPattern.REACT)
        .with_retries(2)
        .build()
    )

    # Test the agent with some questions
    test_questions = [
        'What datasets are available in the project?',
        'Show me information about the public datasets available',
        'What are the most popular baby names in California?',
        'Show me a summary of the BigQuery project structure',
    ]

    for question in test_questions:
        print(f'\n🤖 Question: {question}')
        print('-' * 50)

        try:
            response = await agent.run(question)
            print(f'Answer: {response}')
        except Exception as e:
            print(f'Error: {str(e)}')

        print('-' * 50)


async def main():
    """Main function to run all demonstrations."""

    try:
        print('🚀 Starting BigQuery Tools Demonstration\n')

        # Setup environment
        setup_bigquery_environment()

        # Demonstrate AI agent with tools
        await demonstrate_ai_agent_with_tools()

        print('\n✅ Demonstration completed successfully!')

    except Exception as e:
        print(f'\n❌ Error during demonstration: {str(e)}')


if __name__ == '__main__':
    # Run the demonstration
    asyncio.run(main())
