#!/usr/bin/env python3
"""
Example usage of Redshift tools with flo_ai framework.

This script demonstrates how to:
1. Set up Redshift connection using environment variables
2. Use the Redshift tools with an AI agent
3. Execute various database operations
"""

import asyncio
import os
from flo_ai.builder.agent_builder import AgentBuilder
from flo_ai.models.base_agent import ReasoningPattern
from flo_ai.llm.openai_llm import OpenAI
from flo_ai_tools.tools.redshift_query_tool import (
    execute_redshift_query,
    execute_batch_redshift_queries,
    get_redshift_table_schema,
    list_redshift_tables,
    get_redshift_table_info,
    test_redshift_connection,
    get_redshift_connection_info,
)


def setup_redshift_environment():
    """Setup Redshift environment variables for demonstration."""

    # Set default values for demonstration (in production, these would be set in your environment)
    if not os.getenv('REDSHIFT_HOST'):
        os.environ['REDSHIFT_HOST'] = 'localhost'
    if not os.getenv('REDSHIFT_PORT'):
        os.environ['REDSHIFT_PORT'] = '5439'
    if not os.getenv('REDSHIFT_DATABASE'):
        os.environ['REDSHIFT_DATABASE'] = 'dev'
    if not os.getenv('REDSHIFT_USERNAME'):
        os.environ['REDSHIFT_USERNAME'] = 'admin'
    if not os.getenv('REDSHIFT_PASSWORD'):
        os.environ['REDSHIFT_PASSWORD'] = 'password'

    print('Redshift environment configured:')
    print(f"  Host: {os.getenv('REDSHIFT_HOST')}")
    print(f"  Port: {os.getenv('REDSHIFT_PORT')}")
    print(f"  Database: {os.getenv('REDSHIFT_DATABASE')}")
    print(f"  Username: {os.getenv('REDSHIFT_USERNAME')}")
    print(f"  Password: {'*' * len(os.getenv('REDSHIFT_PASSWORD', ''))}")


async def create_sample_data():
    """Create some sample tables and data for demonstration."""

    # Create a sample users table
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """

    # Create a sample orders table
    create_orders_table = """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10,2) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending'
    )
    """

    # Insert sample data
    insert_users = """
    INSERT INTO users (id, username, email) VALUES 
    (1, 'john_doe', 'john@example.com'),
    (2, 'jane_smith', 'jane@example.com'),
    (3, 'bob_wilson', 'bob@example.com')
    ON CONFLICT (id) DO NOTHING
    """

    insert_orders = """
    INSERT INTO orders (id, user_id, total_amount, status) VALUES 
    (1, 1, 99.99, 'completed'),
    (2, 2, 149.50, 'pending'),
    (3, 1, 75.25, 'completed'),
    (4, 3, 200.00, 'cancelled')
    ON CONFLICT (id) DO NOTHING
    """

    print('Creating sample tables and data...')

    # Execute the creation and insertion queries
    await execute_redshift_query(create_users_table)
    await execute_redshift_query(create_orders_table)
    await execute_redshift_query(insert_users)
    await execute_redshift_query(insert_orders)

    print('Sample data created successfully!')


async def demonstrate_basic_tools():
    """Demonstrate the basic Redshift tools."""

    print('\n=== Demonstrating Basic Redshift Tools ===\n')

    # Get connection info
    print('1. Getting connection information:')
    info_result = await get_redshift_connection_info()
    print(info_result)

    # Test connection
    print('\n2. Testing connection:')
    test_result = await test_redshift_connection()
    print(test_result)

    # List all tables
    print('\n3. Listing all tables:')
    tables_result = await list_redshift_tables()
    print(tables_result)

    # Get table schema
    print('\n4. Getting users table schema:')
    schema_result = await get_redshift_table_schema('users')
    print(schema_result)

    # Get table info
    print('\n5. Getting users table information:')
    info_result = await get_redshift_table_info('users')
    print(info_result)

    # Execute a simple query
    print('\n6. Executing a simple query:')
    query_result = await execute_redshift_query(
        'SELECT COUNT(*) as user_count FROM users'
    )
    print(query_result)

    # Execute a query with parameters
    print('\n7. Executing a parameterized query:')
    param_query = 'SELECT username, email FROM users WHERE is_active = %s'
    param_result = await execute_redshift_query(param_query, '{"is_active": true}')
    print(param_result)


async def demonstrate_ai_agent_with_tools():
    """Demonstrate using Redshift tools with an AI agent."""

    print('\n=== Demonstrating AI Agent with Redshift Tools ===\n')

    # Create an LLM instance (you'll need to set your API key)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('⚠️  OPENAI_API_KEY not set. Skipping AI agent demonstration.')
        return

    llm = OpenAI(model='gpt-4o-mini', api_key=api_key)

    # Create an agent with Redshift tools
    agent = (
        AgentBuilder()
        .with_name('Redshift Data Analyst')
        .with_prompt("""You are a data analyst with access to a Redshift database. 
                        You can execute SQL queries, explore table schemas, and analyze data.
                        Always use the appropriate tools to answer questions about the database.
                        Be helpful and provide clear explanations of your findings.""")
        .with_llm(llm)
        .with_tools(
            [
                execute_redshift_query.tool,
                get_redshift_table_schema.tool,
                list_redshift_tables.tool,
                get_redshift_table_info.tool,
            ]
        )
        .with_reasoning(ReasoningPattern.REACT)
        .with_retries(2)
        .build()
    )

    # Test the agent with some questions
    test_questions = [
        'What tables are available in the database?',
        'Show me the schema of the users table',
        'How many users are there in the database?',
        'What is the total amount of all completed orders?',
        'Show me a summary of the database structure',
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


async def demonstrate_batch_queries():
    """Demonstrate batch query execution."""

    print('\n=== Demonstrating Batch Query Execution ===\n')

    # Define a batch of queries
    batch_queries = [
        'SELECT COUNT(*) as total_users FROM users',
        'SELECT COUNT(*) as total_orders FROM orders',
        'SELECT AVG(total_amount) as avg_order_value FROM orders',
        'SELECT status, COUNT(*) as count FROM orders GROUP BY status',
    ]

    # Execute batch queries
    batch_result = await execute_batch_redshift_queries(str(batch_queries))
    print(batch_result)


async def cleanup():
    """Clean up sample data."""

    print('\n=== Cleaning Up Sample Data ===\n')

    # Drop sample tables
    cleanup_queries = [
        'DROP TABLE IF EXISTS orders CASCADE',
        'DROP TABLE IF EXISTS users CASCADE',
    ]

    for query in cleanup_queries:
        result = await execute_redshift_query(query)
        print(f'Cleanup: {result}')


async def main():
    """Main function to run all demonstrations."""

    try:
        print('🚀 Starting Redshift Tools Demonstration\n')

        # Setup environment
        setup_redshift_environment()

        # Create sample data
        await create_sample_data()

        # Demonstrate basic tools
        await demonstrate_basic_tools()

        # Demonstrate batch queries
        await demonstrate_batch_queries()

        # Demonstrate AI agent with tools
        await demonstrate_ai_agent_with_tools()

        # Cleanup
        await cleanup()

        print('\n✅ Demonstration completed successfully!')

    except Exception as e:
        print(f'\n❌ Error during demonstration: {str(e)}')


if __name__ == '__main__':
    # Run the demonstration
    asyncio.run(main())
