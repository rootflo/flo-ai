"""
BigQuery connector for flo_ai_tools.

This module provides a connection manager for Google Cloud BigQuery
that creates new connections for each operation rather than maintaining
a global connection state.
"""

from typing import Dict, Any, Optional, List
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth import default
from google.api_core import exceptions


class BigQueryConnectionManager:
    """Manages BigQuery connections with connection creation for each operation."""

    def __init__(
        self,
        project_id: str = None,
        credentials_path: str = None,
        location: str = 'US',
        use_default_credentials: bool = True,
    ):
        """
        Initialize BigQuery connection manager.

        Args:
            project_id: Google Cloud project ID (if None, uses default from credentials)
            credentials_path: Path to service account JSON file
            location: BigQuery dataset location (default: 'US')
            use_default_credentials: Whether to use default credentials
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.location = location
        self.use_default_credentials = use_default_credentials
        self._client: Optional[bigquery.Client] = None

    def _get_client(self) -> bigquery.Client:
        """Get a BigQuery client, creating one if it doesn't exist."""
        if self._client is None:
            try:
                if self.credentials_path:
                    # Use service account credentials
                    credentials = service_account.Credentials.from_service_account_file(
                        self.credentials_path
                    )
                    self._client = bigquery.Client(
                        credentials=credentials,
                        project=self.project_id,
                        location=self.location,
                    )
                elif self.use_default_credentials:
                    # Use default credentials (ADC)
                    credentials, project = default()
                    self._client = bigquery.Client(
                        credentials=credentials,
                        project=self.project_id or project,
                        location=self.location,
                    )
                else:
                    raise ValueError(
                        'Either credentials_path or use_default_credentials must be specified'
                    )

            except Exception as e:
                raise ConnectionError(f'Failed to connect to BigQuery: {str(e)}')

        return self._client

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
        client = self._get_client()

        try:
            # Create query job
            job_config = bigquery.QueryJobConfig()

            # Add parameters if provided
            if params:
                query_params = []
                for key, value in params.items():
                    if isinstance(value, str):
                        param = bigquery.ScalarQueryParameter(key, 'STRING', value)
                    elif isinstance(value, int):
                        param = bigquery.ScalarQueryParameter(key, 'INT64', value)
                    elif isinstance(value, float):
                        param = bigquery.ScalarQueryParameter(key, 'FLOAT64', value)
                    elif isinstance(value, bool):
                        param = bigquery.ScalarQueryParameter(key, 'BOOL', value)
                    else:
                        param = bigquery.ScalarQueryParameter(key, 'STRING', str(value))
                    query_params.append(param)

                job_config.query_parameters = query_params

            # Execute query
            query_job = client.query(query, job_config=job_config)

            # Wait for completion
            query_job.result()

            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                # Fetch results
                results = []
                for row in query_job:
                    results.append(tuple(row.values()))

                # Get column names
                column_names = [field.name for field in query_job.schema]

                return {
                    'columns': column_names,
                    'data': results,
                    'row_count': len(results),
                    'total_rows': query_job.total_rows or 0,
                    'total_bytes_processed': query_job.total_bytes_processed or 0,
                }
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                return {
                    'affected_rows': query_job.num_dml_affected_rows or 0,
                    'message': f'Query executed successfully. {query_job.num_dml_affected_rows or 0} rows affected.',
                }

        except exceptions.BigQueryError as e:
            raise Exception(f'BigQuery query execution failed: {str(e)}')
        except Exception as e:
            raise Exception(f'Query execution failed: {str(e)}')

    async def execute_batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in a batch.

        Args:
            queries: List of SQL queries to execute

        Returns:
            List of results for each query
        """
        results = []

        try:
            for query in queries:
                result = await self.execute_query(query)
                results.append({'query': query, 'result': result})
        except Exception as e:
            raise Exception(f'Batch query execution failed: {str(e)}')

        return results

    async def get_table_schema(
        self, dataset_id: str, table_id: str, project_id: str = None
    ) -> Dict[str, Any]:
        """
        Get schema information for a specific table.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            project_id: Project ID (if None, uses default)

        Returns:
            Table schema information
        """
        client = self._get_client()

        try:
            # Construct table reference
            table_ref = f'{project_id or client.project}.{dataset_id}.{table_id}'
            table = client.get_table(table_ref)

            # Extract schema information
            schema_info = []
            for field in table.schema:
                schema_info.append(
                    {
                        'name': field.name,
                        'type': field.field_type,
                        'mode': field.mode,
                        'description': field.description or '',
                        'is_nullable': field.mode == 'NULLABLE',
                    }
                )

            return {
                'table_id': table.table_id,
                'dataset_id': table.dataset_id,
                'project_id': table.project,
                'schema': schema_info,
                'row_count': table.num_rows or 0,
                'size_bytes': table.num_bytes or 0,
                'created': table.created,
                'modified': table.modified,
            }

        except exceptions.NotFound:
            raise Exception(f'Table {dataset_id}.{table_id} not found')
        except Exception as e:
            raise Exception(f'Error getting table schema: {str(e)}')

    async def list_datasets(self, project_id: str = None) -> List[str]:
        """
        List all datasets in a project.

        Args:
            project_id: Project ID (if None, uses default)

        Returns:
            List of dataset IDs
        """
        client = self._get_client()

        try:
            datasets = list(client.list_datasets(project=project_id))
            return [dataset.dataset_id for dataset in datasets]

        except Exception as e:
            raise Exception(f'Error listing datasets: {str(e)}')

    async def list_tables(self, dataset_id: str, project_id: str = None) -> List[str]:
        """
        List all tables in a dataset.

        Args:
            dataset_id: Dataset ID
            project_id: Project ID (if None, uses default)

        Returns:
            List of table IDs
        """
        client = self._get_client()

        try:
            dataset_ref = f'{project_id or client.project}.{dataset_id}'
            tables = list(client.list_tables(dataset_ref))
            return [table.table_id for table in tables]

        except Exception as e:
            raise Exception(f'Error listing tables: {str(e)}')

    async def get_table_info(
        self, dataset_id: str, table_id: str, project_id: str = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive information about a table.

        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            project_id: Project ID (if None, uses default)

        Returns:
            Table information
        """
        try:
            # Get basic schema info
            schema_info = await self.get_table_schema(dataset_id, table_id, project_id)

            # Get additional table details
            client = self._get_client()
            table_ref = f'{project_id or client.project}.{dataset_id}.{table_id}'
            table = client.get_table(table_ref)

            # Format size
            size_gb = (table.num_bytes or 0) / (1024**3)
            size_mb = (table.num_bytes or 0) / (1024**2)

            if size_gb >= 1:
                size_str = f'{size_gb:.2f} GB'
            else:
                size_str = f'{size_mb:.2f} MB'

            return {
                'table_id': table_id,
                'dataset_id': dataset_id,
                'project_id': project_id or client.project,
                'row_count': table.num_rows or 0,
                'size_bytes': table.num_bytes or 0,
                'size_formatted': size_str,
                'created': table.created,
                'modified': table.modified,
                'description': table.description or '',
                'schema': schema_info['schema'],
            }

        except Exception as e:
            raise Exception(f'Error getting table info: {str(e)}')

    async def test_connection(self) -> bool:
        """
        Test the connection to BigQuery.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            client = self._get_client()
            # Try to list datasets to test connection
            list(client.list_datasets(limit=1))
            return True
        except Exception:
            return False

    async def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the current BigQuery project.

        Returns:
            Project information
        """
        client = self._get_client()

        try:
            project = client.project
            datasets = await self.list_datasets(project)

            return {
                'project_id': project,
                'location': self.location,
                'dataset_count': len(datasets),
                'datasets': datasets[:10],  # Show first 10 datasets
                'credentials_type': 'service_account'
                if self.credentials_path
                else 'default',
            }

        except Exception as e:
            raise Exception(f'Error getting project info: {str(e)}')

    async def create_dataset(
        self, dataset_id: str, description: str = None, location: str = None
    ) -> str:
        """
        Create a new dataset.

        Args:
            dataset_id: Dataset ID to create
            description: Optional description
            location: Optional location (if None, uses default)

        Returns:
            Success message
        """
        client = self._get_client()

        try:
            dataset_ref = f'{client.project}.{dataset_id}'
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = location or self.location
            if description:
                dataset.description = description

            dataset = client.create_dataset(dataset, timeout=30)
            return f'Dataset {dataset_id} created successfully in {dataset.location}'

        except Exception as e:
            raise Exception(f'Error creating dataset: {str(e)}')

    async def delete_dataset(
        self, dataset_id: str, delete_contents: bool = False
    ) -> str:
        """
        Delete a dataset.

        Args:
            dataset_id: Dataset ID to delete
            delete_contents: Whether to delete all tables in the dataset

        Returns:
            Success message
        """
        client = self._get_client()

        try:
            dataset_ref = f'{client.project}.{dataset_id}'
            client.delete_dataset(
                dataset_ref, delete_contents=delete_contents, timeout=30
            )
            return f'Dataset {dataset_id} deleted successfully'

        except Exception as e:
            raise Exception(f'Error deleting dataset: {str(e)}')

    def close(self):
        """Close the BigQuery client."""
        if self._client:
            self._client.close()
            self._client = None
