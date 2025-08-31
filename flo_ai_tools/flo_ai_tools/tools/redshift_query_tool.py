import json
import pandas as pd
import os
from typing import Optional
from flo_ai.tool import flo_tool
from flo_ai_tools.connectors.redshift_connector import RedshiftConnectionManager


def get_redshift_connection_manager() -> RedshiftConnectionManager:
    """
    Get a Redshift connection manager using environment variables.

    Returns:
        RedshiftConnectionManager instance

    Raises:
        ValueError: If required environment variables are not set
    """
    # Get connection details from environment variables
    host = os.getenv('REDSHIFT_HOST')
    if not host:
        raise ValueError('REDSHIFT_HOST environment variable is required')

    port = int(os.getenv('REDSHIFT_PORT', '5439'))
    database = os.getenv('REDSHIFT_DATABASE')
    username = os.getenv('REDSHIFT_USERNAME')
    password = os.getenv('REDSHIFT_PASSWORD')
    cluster_identifier = os.getenv('REDSHIFT_CLUSTER_IDENTIFIER')
    iam_profile = os.getenv('REDSHIFT_IAM_PROFILE')

    # Validate required parameters
    if not database:
        raise ValueError('REDSHIFT_DATABASE environment variable is required')

    if cluster_identifier and iam_profile:
        # IAM authentication
        if not username and not password:
            pass  # IAM auth doesn't need username/password
        else:
            raise ValueError('Cannot use both IAM authentication and username/password')
    elif username and password:
        # Username/password authentication
        pass
    else:
        raise ValueError(
            'Either REDSHIFT_USERNAME/REDSHIFT_PASSWORD or REDSHIFT_CLUSTER_IDENTIFIER/REDSHIFT_IAM_PROFILE must be set'
        )

    return RedshiftConnectionManager(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        cluster_identifier=cluster_identifier,
        iam_profile=iam_profile,
    )


@flo_tool(
    description='Execute a SQL query on Redshift database and return results',
    parameter_descriptions={
        'query': 'The SQL query to execute',
        'params': 'Optional parameters for the query (JSON string)',
    },
)
async def execute_redshift_query(query: str, params: Optional[str] = None) -> str:
    """
    Execute a SQL query on the Redshift database.

    Args:
        query: The SQL query to execute
        params: Optional JSON string containing query parameters

    Returns:
        Query results as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Parse parameters if provided
        query_params = None
        if params:
            try:
                query_params = json.loads(params)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format for parameters')

        # Execute the query
        result = await connection_manager.execute_query(query, query_params)

        # Format the result
        if 'columns' in result:  # SELECT query
            if result['row_count'] == 0:
                return f"Query executed successfully. No rows returned.\nColumns: {', '.join(result['columns'])}"

            # Convert to pandas DataFrame for better formatting
            df = pd.DataFrame(result['data'], columns=result['columns'])

            # Format the output
            output = (
                f"Query executed successfully. {result['row_count']} rows returned.\n\n"
            )
            output += f"Columns: {', '.join(result['columns'])}\n\n"

            # Show first 10 rows
            if len(df) > 10:
                output += 'First 10 rows:\n'
                output += df.head(10).to_string(index=False)
                output += f'\n\n... and {len(df) - 10} more rows'
            else:
                output += 'All rows:\n'
                output += df.to_string(index=False)

            return output
        else:  # Non-SELECT query
            return result['message']

    except Exception as e:
        return f'Error executing query: {str(e)}'


@flo_tool(
    description='Execute multiple SQL queries in a batch on Redshift database',
    parameter_descriptions={'queries': 'JSON array of SQL queries to execute'},
)
async def execute_batch_redshift_queries(queries: str) -> str:
    """
    Execute multiple SQL queries in a batch.

    Args:
        queries: JSON string containing an array of SQL queries

    Returns:
        Results of all queries as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Parse queries
        try:
            query_list = json.loads(queries)
            if not isinstance(query_list, list):
                raise ValueError('Queries must be a JSON array')
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON format for queries')

        # Execute batch queries
        results = await connection_manager.execute_batch_queries(query_list)

        # Format the output
        output = f'Batch execution completed. {len(results)} queries processed.\n\n'

        for i, result in enumerate(results, 1):
            output += f"Query {i}: {result['query'][:100]}...\n"
            if 'columns' in result['result']:
                output += f"  Result: {result['result']['row_count']} rows returned\n"
            else:
                output += f"  Result: {result['result']['message']}\n"
            output += '\n'

        return output

    except Exception as e:
        return f'Error executing batch queries: {str(e)}'


@flo_tool(
    description='Get schema information for a Redshift table',
    parameter_descriptions={'table_name': 'Name of the table to get schema for'},
)
async def get_redshift_table_schema(table_name: str) -> str:
    """
    Get detailed schema information for a Redshift table.

    Args:
        table_name: Name of the table

    Returns:
        Table schema information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Get table schema
        schema = await connection_manager.get_table_schema(table_name)

        if not schema['data']:
            return f"No schema information found for table '{table_name}'"

        # Format the output
        output = f"Schema for table '{table_name}':\n\n"
        output += f"{'Column Name':<20} {'Data Type':<20} {'Nullable':<10} {'Default':<15} {'Length':<10}\n"
        output += '-' * 80 + '\n'

        for row in schema['data']:
            column_name = row[0][:19] if len(row[0]) > 19 else row[0]
            data_type = row[1][:19] if len(str(row[1])) > 19 else str(row[1])
            nullable = row[2][:9] if len(str(row[2])) > 9 else str(row[2])
            default_val = str(row[3])[:14] if row[3] else 'NULL'
            length = str(row[4])[:9] if row[4] else 'N/A'

            output += f'{column_name:<20} {data_type:<20} {nullable:<10} {default_val:<15} {length:<10}\n'

        return output

    except Exception as e:
        return f'Error getting table schema: {str(e)}'


@flo_tool(
    description='List all tables in a Redshift schema',
    parameter_descriptions={'schema': "Schema name (default: 'public')"},
)
async def list_redshift_tables(schema: str = 'public') -> str:
    """
    List all tables in a Redshift schema.

    Args:
        schema: Schema name (default: 'public')

    Returns:
        List of tables as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # List tables
        tables = await connection_manager.list_tables(schema)

        if not tables:
            return f"No tables found in schema '{schema}'"

        # Format the output
        output = f"Tables in schema '{schema}':\n\n"
        for i, table in enumerate(tables, 1):
            output += f'{i:2d}. {table}\n'

        output += f'\nTotal: {len(tables)} tables'
        return output

    except Exception as e:
        return f'Error listing tables: {str(e)}'


@flo_tool(
    description='Get comprehensive information about a Redshift table including row count and size',
    parameter_descriptions={'table_name': 'Name of the table to get information for'},
)
async def get_redshift_table_info(table_name: str) -> str:
    """
    Get comprehensive information about a Redshift table.

    Args:
        table_name: Name of the table

    Returns:
        Table information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Get table info
        info = await connection_manager.get_table_info(table_name)

        # Format the output
        output = f"Table Information for '{table_name}':\n\n"
        output += f"Row Count: {info['row_count']:,}\n"
        output += f"Table Size: {info['table_size']}\n"
        output += f"Data Size: {info['data_size']}\n\n"

        # Add schema information
        if info['schema']['data']:
            output += 'Schema:\n'
            output += f"{'Column':<20} {'Type':<20} {'Nullable':<10} {'Default':<15}\n"
            output += '-' * 70 + '\n'

            for row in info['schema']['data']:
                column = row[0][:19] if len(row[0]) > 19 else row[0]
                data_type = row[1][:19] if len(str(row[1])) > 19 else str(row[1])
                nullable = row[2][:9] if len(str(row[2])) > 9 else str(row[2])
                default_val = str(row[3])[:14] if row[3] else 'NULL'

                output += (
                    f'{column:<20} {data_type:<20} {nullable:<10} {default_val:<15}\n'
                )

        return output

    except Exception as e:
        return f'Error getting table info: {str(e)}'


@flo_tool(
    description='Test the Redshift connection and return connection status',
    parameter_descriptions={},
)
async def test_redshift_connection() -> str:
    """
    Test the Redshift connection and return connection status.

    Returns:
        Connection status as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Test connection
        if await connection_manager.test_connection():
            return '✅ Redshift connection is working correctly!'
        else:
            return '❌ Redshift connection test failed'

    except Exception as e:
        return f'❌ Redshift connection test failed: {str(e)}'


@flo_tool(
    description='Get Redshift connection configuration information',
    parameter_descriptions={},
)
async def get_redshift_connection_info() -> str:
    """
    Get information about the current Redshift connection configuration.

    Returns:
        Connection configuration information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_redshift_connection_manager()

        # Format the output
        output = 'Redshift Connection Configuration:\n\n'
        output += f'Host: {connection_manager.host}\n'
        output += f'Port: {connection_manager.port}\n'
        output += f'Database: {connection_manager.database}\n'

        if connection_manager.username and connection_manager.password:
            output += 'Authentication: Username/Password\n'
            output += f'Username: {connection_manager.username}\n'
            output += 'Password: [HIDDEN]\n'
        elif connection_manager.cluster_identifier and connection_manager.iam_profile:
            output += 'Authentication: IAM\n'
            output += f'Cluster Identifier: {connection_manager.cluster_identifier}\n'
            output += f'IAM Profile: {connection_manager.iam_profile}\n'
        else:
            output += 'Authentication: [NOT CONFIGURED]\n'

        return output

    except Exception as e:
        return f'Error getting connection info: {str(e)}'
