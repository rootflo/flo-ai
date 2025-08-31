"""
flo_ai_tools package.

This package provides database and service tools for the flo_ai framework.
"""

# Import connectors
from .connectors import RedshiftConnectionManager, BigQueryConnectionManager

# Import Redshift tools
from .tools.redshift_query_tool import (
    execute_redshift_query,
    execute_batch_redshift_queries,
    get_redshift_table_schema,
    list_redshift_tables,
    get_redshift_table_info,
    test_redshift_connection,
    get_redshift_connection_info,
)

# Import BigQuery tools
from .tools.bigquery_tools import (
    execute_bigquery_query,
    execute_batch_bigquery_queries,
    get_bigquery_table_schema,
    list_bigquery_datasets,
    list_bigquery_tables,
    get_bigquery_table_info,
    test_bigquery_connection,
    get_bigquery_project_info,
    create_bigquery_dataset,
    delete_bigquery_dataset,
)

# Export all tools and connectors
__all__ = [
    # Connectors
    'RedshiftConnectionManager',
    'BigQueryConnectionManager',
    # Redshift Tools
    'execute_redshift_query',
    'execute_batch_redshift_queries',
    'get_redshift_table_schema',
    'list_redshift_tables',
    'get_redshift_table_info',
    'test_redshift_connection',
    'get_redshift_connection_info',
    # BigQuery Tools
    'execute_bigquery_query',
    'execute_batch_bigquery_queries',
    'get_bigquery_table_schema',
    'list_bigquery_datasets',
    'list_bigquery_tables',
    'get_bigquery_table_info',
    'test_bigquery_connection',
    'get_bigquery_project_info',
    'create_bigquery_dataset',
    'delete_bigquery_dataset',
]
