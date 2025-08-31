import json
import pandas as pd
import os
from typing import Optional
from flo_ai.tool import flo_tool
from flo_ai_tools.connectors.bigquery_connector import BigQueryConnectionManager


def get_bigquery_connection_manager() -> BigQueryConnectionManager:
    """
    Get a BigQuery connection manager using environment variables.

    Returns:
        BigQueryConnectionManager instance

    Raises:
        ValueError: If required environment variables are not set
    """
    # Get connection details from environment variables
    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    credentials_path = os.getenv('BIGQUERY_CREDENTIALS_PATH')
    location = os.getenv('BIGQUERY_LOCATION', 'US')
    use_default_credentials = (
        os.getenv('BIGQUERY_USE_DEFAULT_CREDENTIALS', 'true').lower() == 'true'
    )

    # Validate required parameters
    if not project_id and not use_default_credentials:
        raise ValueError(
            'Either BIGQUERY_PROJECT_ID or BIGQUERY_USE_DEFAULT_CREDENTIALS must be set'
        )

    return BigQueryConnectionManager(
        project_id=project_id,
        credentials_path=credentials_path,
        location=location,
        use_default_credentials=use_default_credentials,
    )


@flo_tool(
    description='Execute a SQL query on BigQuery and return results',
    parameter_descriptions={
        'query': 'The SQL query to execute',
        'params': 'Optional parameters for the query (JSON string)',
    },
)
async def execute_bigquery_query(query: str, params: Optional[str] = None) -> str:
    """
    Execute a SQL query on BigQuery.

    Args:
        query: The SQL query to execute
        params: Optional JSON string containing query parameters

    Returns:
        Query results as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

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
                output = 'Query executed successfully. No rows returned.\n'
                output += f"Columns: {', '.join(result['columns'])}\n"
                output += f"Total rows in table: {result['total_rows']:,}\n"
                output += f"Bytes processed: {result['total_bytes_processed']:,}"
                return output

            # Convert to pandas DataFrame for better formatting
            df = pd.DataFrame(result['data'], columns=result['columns'])

            # Format the output
            output = (
                f"Query executed successfully. {result['row_count']} rows returned.\n\n"
            )
            output += f"Columns: {', '.join(result['columns'])}\n"
            output += f"Total rows in table: {result['total_rows']:,}\n"
            output += f"Bytes processed: {result['total_bytes_processed']:,}\n\n"

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
    description='Execute multiple SQL queries in a batch on BigQuery',
    parameter_descriptions={'queries': 'JSON array of SQL queries to execute'},
)
async def execute_batch_bigquery_queries(queries: str) -> str:
    """
    Execute multiple SQL queries in a batch.

    Args:
        queries: JSON string containing an array of SQL queries

    Returns:
        Results of all queries as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

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
                output += f"  Bytes processed: {result['result']['total_bytes_processed']:,}\n"
            else:
                output += f"  Result: {result['result']['message']}\n"
            output += '\n'

        return output

    except Exception as e:
        return f'Error executing batch queries: {str(e)}'


@flo_tool(
    description='Get schema information for a BigQuery table',
    parameter_descriptions={
        'dataset_id': 'Dataset ID containing the table',
        'table_id': 'Name of the table to get schema for',
        'project_id': 'Optional project ID (uses default if not specified)',
    },
)
async def get_bigquery_table_schema(
    dataset_id: str, table_id: str, project_id: str = None
) -> str:
    """
    Get detailed schema information for a BigQuery table.

    Args:
        dataset_id: Dataset ID containing the table
        table_id: Name of the table
        project_id: Optional project ID

    Returns:
        Table schema information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Get table schema
        schema = await connection_manager.get_table_schema(
            dataset_id, table_id, project_id
        )

        if not schema['schema']:
            return f'No schema information found for table {dataset_id}.{table_id}'

        # Format the output
        output = f"Schema for table {schema['project_id']}.{dataset_id}.{table_id}:\n\n"
        output += f"Row Count: {schema['row_count']:,}\n"
        output += f"Size: {schema['size_bytes']:,} bytes\n"
        output += f"Created: {schema['created']}\n"
        output += f"Modified: {schema['modified']}\n\n"

        output += f"{'Column Name':<25} {'Data Type':<15} {'Mode':<10} {'Nullable':<10} {'Description':<30}\n"
        output += '-' * 100 + '\n'

        for field in schema['schema']:
            column_name = (
                field['name'][:24] if len(field['name']) > 24 else field['name']
            )
            data_type = field['type'][:14] if len(field['type']) > 14 else field['type']
            mode = field['mode'][:9] if len(field['mode']) > 9 else field['mode']
            nullable = 'YES' if field['is_nullable'] else 'NO'
            description = (
                field['description'][:29]
                if field['description'] and len(field['description']) > 29
                else field['description'] or ''
            )

            output += f'{column_name:<25} {data_type:<15} {mode:<10} {nullable:<10} {description:<30}\n'

        return output

    except Exception as e:
        return f'Error getting table schema: {str(e)}'


@flo_tool(
    description='List all datasets in a BigQuery project',
    parameter_descriptions={
        'project_id': 'Optional project ID (uses default if not specified)'
    },
)
async def list_bigquery_datasets(project_id: str = None) -> str:
    """
    List all datasets in a BigQuery project.

    Args:
        project_id: Optional project ID

    Returns:
        List of datasets as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # List datasets
        datasets = await connection_manager.list_datasets(project_id)

        if not datasets:
            project = project_id or connection_manager.project_id or 'default'
            return f"No datasets found in project '{project}'"

        # Format the output
        project = project_id or connection_manager.project_id or 'default'
        output = f"Datasets in project '{project}':\n\n"
        for i, dataset in enumerate(datasets, 1):
            output += f'{i:2d}. {dataset}\n'

        output += f'\nTotal: {len(datasets)} datasets'
        return output

    except Exception as e:
        return f'Error listing datasets: {str(e)}'


@flo_tool(
    description='List all tables in a BigQuery dataset',
    parameter_descriptions={
        'dataset_id': 'Dataset ID to list tables from',
        'project_id': 'Optional project ID (uses default if not specified)',
    },
)
async def list_bigquery_tables(dataset_id: str, project_id: str = None) -> str:
    """
    List all tables in a BigQuery dataset.

    Args:
        dataset_id: Dataset ID
        project_id: Optional project ID

    Returns:
        List of tables as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # List tables
        tables = await connection_manager.list_tables(dataset_id, project_id)

        if not tables:
            project = project_id or connection_manager.project_id or 'default'
            return f"No tables found in dataset '{project}.{dataset_id}'"

        # Format the output
        project = project_id or connection_manager.project_id or 'default'
        output = f"Tables in dataset '{project}.{dataset_id}':\n\n"
        for i, table in enumerate(tables, 1):
            output += f'{i:2d}. {table}\n'

        output += f'\nTotal: {len(tables)} tables'
        return output

    except Exception as e:
        return f'Error listing tables: {str(e)}'


@flo_tool(
    description='Get comprehensive information about a BigQuery table including row count and size',
    parameter_descriptions={
        'dataset_id': 'Dataset ID containing the table',
        'table_id': 'Name of the table to get information for',
        'project_id': 'Optional project ID (uses default if not specified)',
    },
)
async def get_bigquery_table_info(
    dataset_id: str, table_id: str, project_id: str = None
) -> str:
    """
    Get comprehensive information about a BigQuery table.

    Args:
        dataset_id: Dataset ID containing the table
        table_id: Name of the table
        project_id: Optional project ID

    Returns:
        Table information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Get table info
        info = await connection_manager.get_table_info(dataset_id, table_id, project_id)

        # Format the output
        output = (
            f"Table Information for {info['project_id']}.{dataset_id}.{table_id}:\n\n"
        )
        output += f"Row Count: {info['row_count']:,}\n"
        output += f"Size: {info['size_formatted']}\n"
        output += f"Created: {info['created']}\n"
        output += f"Modified: {info['modified']}\n"
        if info['description']:
            output += f"Description: {info['description']}\n"
        output += '\n'

        # Add schema information
        if info['schema']:
            output += 'Schema:\n'
            output += f"{'Column':<25} {'Type':<15} {'Mode':<10} {'Nullable':<10} {'Description':<30}\n"
            output += '-' * 100 + '\n'

            for field in info['schema']:
                column = (
                    field['name'][:24] if len(field['name']) > 24 else field['name']
                )
                data_type = (
                    field['type'][:14] if len(field['type']) > 14 else field['type']
                )
                mode = field['mode'][:9] if len(field['mode']) > 9 else field['mode']
                nullable = 'YES' if field['is_nullable'] else 'NO'
                description = (
                    field['description'][:29]
                    if field['description'] and len(field['description']) > 29
                    else field['description'] or ''
                )

                output += f'{column:<25} {data_type:<15} {mode:<10} {nullable:<10} {description:<30}\n'

        return output

    except Exception as e:
        return f'Error getting table info: {str(e)}'


@flo_tool(
    description='Test the BigQuery connection and return connection status',
    parameter_descriptions={},
)
async def test_bigquery_connection() -> str:
    """
    Test the BigQuery connection and return connection status.

    Returns:
        Connection status as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Test connection
        if await connection_manager.test_connection():
            return '✅ BigQuery connection is working correctly!'
        else:
            return '❌ BigQuery connection test failed'

    except Exception as e:
        return f'❌ BigQuery connection test failed: {str(e)}'


@flo_tool(
    description='Get BigQuery project information and connection configuration',
    parameter_descriptions={},
)
async def get_bigquery_project_info() -> str:
    """
    Get information about the current BigQuery project and connection.

    Returns:
        Project information as a formatted string
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Get project info
        info = await connection_manager.get_project_info()

        # Format the output
        output = 'BigQuery Project Information:\n\n'
        output += f"Project ID: {info['project_id']}\n"
        output += f"Location: {info['location']}\n"
        output += f"Dataset Count: {info['dataset_count']}\n"
        output += f"Credentials Type: {info['credentials_type']}\n\n"

        if info['datasets']:
            output += 'Available Datasets:\n'
            for i, dataset in enumerate(info['datasets'], 1):
                output += f'  {i:2d}. {dataset}\n'

            if info['dataset_count'] > 10:
                output += f"  ... and {info['dataset_count'] - 10} more datasets"

        return output

    except Exception as e:
        return f'Error getting project info: {str(e)}'


@flo_tool(
    description='Create a new BigQuery dataset',
    parameter_descriptions={
        'dataset_id': 'Dataset ID to create',
        'description': 'Optional description for the dataset',
        'location': 'Optional location (uses default if not specified)',
    },
)
async def create_bigquery_dataset(
    dataset_id: str, description: str = None, location: str = None
) -> str:
    """
    Create a new BigQuery dataset.

    Args:
        dataset_id: Dataset ID to create
        description: Optional description
        location: Optional location

    Returns:
        Success message
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Create dataset
        result = await connection_manager.create_dataset(
            dataset_id, description, location
        )
        return f'✅ {result}'

    except Exception as e:
        return f'❌ Error creating dataset: {str(e)}'


@flo_tool(
    description='Delete a BigQuery dataset',
    parameter_descriptions={
        'dataset_id': 'Dataset ID to delete',
        'delete_contents': 'Whether to delete all tables in the dataset (true/false)',
    },
)
async def delete_bigquery_dataset(
    dataset_id: str, delete_contents: str = 'false'
) -> str:
    """
    Delete a BigQuery dataset.

    Args:
        dataset_id: Dataset ID to delete
        delete_contents: Whether to delete all tables (true/false)

    Returns:
        Success message
    """
    try:
        # Get connection manager
        connection_manager = get_bigquery_connection_manager()

        # Parse delete_contents parameter
        try:
            should_delete = json.loads(delete_contents.lower())
        except (json.JSONDecodeError, TypeError):
            should_delete = delete_contents.lower() == 'true'

        # Delete dataset
        result = await connection_manager.delete_dataset(dataset_id, should_delete)
        return f'✅ {result}'

    except Exception as e:
        return f'❌ Error deleting dataset: {str(e)}'
