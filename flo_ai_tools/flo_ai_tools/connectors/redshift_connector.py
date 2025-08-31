"""
Redshift connector for flo_ai_tools.

This module provides a connection manager for Amazon Redshift databases
that creates new connections for each operation rather than maintaining
a global connection state.
"""

from typing import Dict, Any, Optional, List
from redshift_connector import connect
from contextlib import asynccontextmanager
from flo_ai.utils.logger import logger


class RedshiftConnectionManager:
    """Manages Redshift database connections with connection creation for each operation."""

    def __init__(
        self,
        host: str,
        port: int = 5439,
        database: str = None,
        username: str = None,
        password: str = None,
        cluster_identifier: str = None,
        iam_profile: str = None,
    ):
        """
        Initialize Redshift connection manager.

        Args:
            host: Redshift cluster endpoint
            port: Redshift port (default: 5439)
            database: Database name
            username: Username for authentication
            password: Password for authentication
            cluster_identifier: Redshift cluster identifier for IAM auth
            iam_profile: IAM profile name for IAM authentication
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.cluster_identifier = cluster_identifier
        self.iam_profile = iam_profile

    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection, creating a new one for each operation."""
        connection = None
        try:
            if self.iam_profile:
                # IAM authentication
                connection = connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    cluster_identifier=self.cluster_identifier,
                    iam_profile=self.iam_profile,
                )
            else:
                # Username/password authentication
                connection = connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.username,
                    password=self.password,
                )

            # Test the connection
            cursor = connection.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()

            yield connection

        except Exception as e:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    logger.error(f'Failed to close connection: {str(e)}')
                    pass
            raise ConnectionError(f'Failed to connect to Redshift: {str(e)}')
        finally:
            if connection and not connection.closed:
                connection.close()

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Optional parameters for the query

        Returns:
            Query results
        """
        async with self.get_connection() as connection:
            cursor = connection.cursor()

            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                # Check if it's a SELECT query
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description]
                    return {
                        'columns': column_names,
                        'data': results,
                        'row_count': len(results),
                    }
                else:
                    # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                    connection.commit()
                    return {
                        'affected_rows': cursor.rowcount,
                        'message': f'Query executed successfully. {cursor.rowcount} rows affected.',
                    }

            except Exception as e:
                connection.rollback()
                raise Exception(f'Query execution failed: {str(e)}')
            finally:
                cursor.close()

    async def execute_batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in a batch.

        Args:
            queries: List of SQL queries to execute

        Returns:
            List of results for each query
        """
        results = []

        async with self.get_connection() as connection:
            try:
                for query in queries:
                    result = await self.execute_query(query)
                    results.append({'query': query, 'result': result})
            except Exception as e:
                connection.rollback()
                raise Exception(f'Batch query execution failed: {str(e)}')

        return results

    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Table schema information
        """
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_name = %s
        ORDER BY ordinal_position
        """

        result = await self.execute_query(query, {'table_name': table_name})
        return result

    async def list_tables(self, schema: str = 'public') -> List[str]:
        """
        List all tables in a schema.

        Args:
            schema: Schema name (default: 'public')

        Returns:
            List of table names
        """
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        result = await self.execute_query(query, {'schema': schema})
        return [row[0] for row in result['data']] if result['data'] else []

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a table.

        Args:
            table_name: Name of the table

        Returns:
            Table information including row count and size
        """
        # Get row count
        count_query = f'SELECT COUNT(*) FROM {table_name}'
        count_result = await self.execute_query(count_query)
        row_count = count_result['data'][0][0] if count_result['data'] else 0

        # Get table size
        size_query = """
        SELECT 
            pg_size_pretty(pg_total_relation_size(%s)) as table_size,
            pg_size_pretty(pg_relation_size(%s)) as data_size
        """
        size_result = await self.execute_query(
            size_query, {'table_name': table_name, 'table_name2': table_name}
        )
        table_size = size_result['data'][0][0] if size_result['data'] else 'Unknown'
        data_size = size_result['data'][0][1] if size_result['data'] else 'Unknown'

        # Get schema
        schema = await self.get_table_schema(table_name)

        return {
            'table_name': table_name,
            'row_count': row_count,
            'table_size': table_size,
            'data_size': data_size,
            'schema': schema,
        }

    async def test_connection(self) -> bool:
        """
        Test the connection to Redshift.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            async with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT 1 as test')
                result = cursor.fetchone()
                cursor.close()
                return result and result[0] == 1
        except Exception:
            return False
