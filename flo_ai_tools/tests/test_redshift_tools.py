#!/usr/bin/env python3
"""
Tests for Redshift tools integration with flo_ai framework.
"""

import pytest
import os
from unittest.mock import Mock, patch
from flo_ai_tools.connectors.redshift_connector import RedshiftConnectionManager
from flo_ai_tools.tools.redshift_query_tool import (
    get_redshift_connection_manager,
    execute_redshift_query,
    execute_batch_redshift_queries,
    get_redshift_table_schema,
    list_redshift_tables,
    get_redshift_table_info,
    test_redshift_connection,
    get_redshift_connection_info,
)


class TestRedshiftConnectionManager:
    """Test the RedshiftConnectionManager class."""

    def test_init(self):
        """Test RedshiftConnectionManager initialization."""
        manager = RedshiftConnectionManager(
            host='test-host',
            port=5439,
            database='test_db',
            username='test_user',
            password='test_pass',
        )

        assert manager.host == 'test-host'
        assert manager.port == 5439
        assert manager.database == 'test_db'
        assert manager.username == 'test_user'
        assert manager.password == 'test_pass'

    def test_init_with_iam(self):
        """Test RedshiftConnectionManager initialization with IAM."""
        manager = RedshiftConnectionManager(
            host='test-host',
            port=5439,
            database='test_db',
            cluster_identifier='test-cluster',
            iam_profile='test-profile',
        )

        assert manager.cluster_identifier == 'test-cluster'
        assert manager.iam_profile == 'test-profile'
        assert manager.username is None
        assert manager.password is None

    @pytest.mark.asyncio
    async def test_get_connection_context_manager(self):
        """Test that get_connection works as an async context manager."""
        manager = RedshiftConnectionManager(
            host='test-host',
            database='test_db',
            username='test_user',
            password='test_pass',
        )

        # Mock the connect function
        with patch(
            'flo_ai_tools.connectors.redshift_connector.connect'
        ) as mock_connect:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (1,)
            mock_connect.return_value = mock_connection

            async with manager.get_connection() as connection:
                assert connection == mock_connection

            # Verify connection was closed
            mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query(self):
        """Test query execution."""
        manager = RedshiftConnectionManager(
            host='test-host',
            database='test_db',
            username='test_user',
            password='test_pass',
        )

        # Mock the connection context manager
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [(1, 'John'), (2, 'Jane')]

        with patch.object(manager, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection

            result = await manager.execute_query('SELECT * FROM users')

            assert result['columns'] == ['id', 'name']
            assert result['data'] == [(1, 'John'), (2, 'Jane')]
            assert result['row_count'] == 2


class TestRedshiftTools:
    """Test the Redshift tools with flo_ai integration."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Set up test environment variables
        self.original_env = {}
        for key in [
            'REDSHIFT_HOST',
            'REDSHIFT_DATABASE',
            'REDSHIFT_USERNAME',
            'REDSHIFT_PASSWORD',
        ]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]

        # Set test environment variables
        os.environ['REDSHIFT_HOST'] = 'test-host'
        os.environ['REDSHIFT_DATABASE'] = 'test_db'
        os.environ['REDSHIFT_USERNAME'] = 'test_user'
        os.environ['REDSHIFT_PASSWORD'] = 'test_pass'

    def teardown_method(self):
        """Clean up test environment."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value
        else:
            # Remove test environment variables
            for key in [
                'REDSHIFT_HOST',
                'REDSHIFT_DATABASE',
                'REDSHIFT_USERNAME',
                'REDSHIFT_PASSWORD',
            ]:
                if key in os.environ:
                    del os.environ[key]

    def test_get_redshift_connection_manager_success(self):
        """Test successful connection manager creation."""
        manager = get_redshift_connection_manager()

        assert isinstance(manager, RedshiftConnectionManager)
        assert manager.host == 'test-host'
        assert manager.database == 'test_db'
        assert manager.username == 'test_user'
        assert manager.password == 'test_pass'

    def test_get_redshift_connection_manager_missing_host(self):
        """Test connection manager creation with missing host."""
        del os.environ['REDSHIFT_HOST']

        with pytest.raises(
            ValueError, match='REDSHIFT_HOST environment variable is required'
        ):
            get_redshift_connection_manager()

    def test_get_redshift_connection_manager_missing_database(self):
        """Test connection manager creation with missing database."""
        del os.environ['REDSHIFT_DATABASE']

        with pytest.raises(
            ValueError, match='REDSHIFT_DATABASE environment variable is required'
        ):
            get_redshift_connection_manager()

    def test_get_redshift_connection_manager_iam_auth(self):
        """Test connection manager creation with IAM authentication."""
        # Set IAM environment variables
        del os.environ['REDSHIFT_USERNAME']
        del os.environ['REDSHIFT_PASSWORD']
        os.environ['REDSHIFT_CLUSTER_IDENTIFIER'] = 'test-cluster'
        os.environ['REDSHIFT_IAM_PROFILE'] = 'test-profile'

        manager = get_redshift_connection_manager()

        assert manager.cluster_identifier == 'test-cluster'
        assert manager.iam_profile == 'test-profile'
        assert manager.username is None
        assert manager.password is None

    def test_get_redshift_connection_manager_mixed_auth_error(self):
        """Test connection manager creation with mixed authentication (should fail)."""
        os.environ['REDSHIFT_CLUSTER_IDENTIFIER'] = 'test-cluster'
        os.environ['REDSHIFT_IAM_PROFILE'] = 'test-profile'

        with pytest.raises(
            ValueError, match='Cannot use both IAM authentication and username/password'
        ):
            get_redshift_connection_manager()

    def test_get_redshift_connection_manager_no_auth_error(self):
        """Test connection manager creation with no authentication (should fail)."""
        del os.environ['REDSHIFT_USERNAME']
        del os.environ['REDSHIFT_PASSWORD']

        with pytest.raises(
            ValueError,
            match='Either REDSHIFT_USERNAME/REDSHIFT_PASSWORD or REDSHIFT_CLUSTER_IDENTIFIER/REDSHIFT_IAM_PROFILE must be set',
        ):
            get_redshift_connection_manager()

    @pytest.mark.asyncio
    async def test_execute_redshift_query_success(self):
        """Test successful query execution."""
        # Mock the connection manager
        mock_manager = Mock()
        mock_result = {
            'columns': ['id', 'name'],
            'data': [(1, 'John'), (2, 'Jane')],
            'row_count': 2,
        }
        mock_manager.execute_query.return_value = mock_result

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await execute_redshift_query('SELECT * FROM users')

            assert '2 rows returned' in result
            assert 'John' in result
            assert 'Jane' in result
            mock_manager.execute_query.assert_called_once_with(
                'SELECT * FROM users', None
            )

    @pytest.mark.asyncio
    async def test_execute_redshift_query_with_params(self):
        """Test query execution with parameters."""
        mock_manager = Mock()
        mock_result = {'columns': ['id', 'name'], 'data': [(1, 'John')], 'row_count': 1}
        mock_manager.execute_query.return_value = mock_result

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await execute_redshift_query(
                'SELECT * FROM users WHERE id = %s', '{"id": 1}'
            )

            assert '1 row returned' in result
            mock_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_redshift_query_invalid_json_params(self):
        """Test query execution with invalid JSON parameters."""
        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager'
        ):
            result = await execute_redshift_query(
                'SELECT * FROM users WHERE id = %s', 'invalid json'
            )

            assert 'Invalid JSON format for parameters' in result

    @pytest.mark.asyncio
    async def test_execute_batch_redshift_queries(self):
        """Test batch query execution."""
        mock_manager = Mock()
        mock_results = [
            {'query': 'SELECT 1', 'result': {'row_count': 1}},
            {'query': 'SELECT 2', 'result': {'row_count': 1}},
        ]
        mock_manager.execute_batch_queries.return_value = mock_results

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await execute_batch_redshift_queries('["SELECT 1", "SELECT 2"]')

            assert '2 queries processed' in result
            mock_manager.execute_batch_queries.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_batch_redshift_queries_invalid_json(self):
        """Test batch query execution with invalid JSON."""
        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager'
        ):
            result = await execute_batch_redshift_queries('invalid json')

            assert 'Invalid JSON format for queries' in result

    @pytest.mark.asyncio
    async def test_get_redshift_table_schema(self):
        """Test getting table schema."""
        mock_manager = Mock()
        mock_schema = {
            'data': [
                ('id', 'integer', 'NO', None, None, None, None),
                ('name', 'varchar', 'YES', None, 50, None, None),
            ]
        }
        mock_manager.get_table_schema.return_value = mock_schema

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await get_redshift_table_schema('users')

            assert "Schema for table 'users'" in result
            assert 'id' in result
            assert 'name' in result
            mock_manager.get_table_schema.assert_called_once_with('users')

    @pytest.mark.asyncio
    async def test_list_redshift_tables(self):
        """Test listing tables."""
        mock_manager = Mock()
        mock_tables = ['users', 'orders', 'products']
        mock_manager.list_tables.return_value = mock_tables

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await list_redshift_tables('public')

            assert '3 tables' in result
            assert 'users' in result
            assert 'orders' in result
            assert 'products' in result
            mock_manager.list_tables.assert_called_once_with('public')

    @pytest.mark.asyncio
    async def test_get_redshift_table_info(self):
        """Test getting table information."""
        mock_manager = Mock()
        mock_info = {
            'table_name': 'users',
            'row_count': 100,
            'table_size': '1 MB',
            'data_size': '500 KB',
            'schema': {
                'data': [
                    ('id', 'integer', 'NO', None, None, None, None),
                    ('name', 'varchar', 'YES', None, 50, None, None),
                ]
            },
        }
        mock_manager.get_table_info.return_value = mock_info

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await get_redshift_table_info('users')

            assert "Table Information for 'users'" in result
            assert '100' in result
            assert '1 MB' in result
            mock_manager.get_table_info.assert_called_once_with('users')

    @pytest.mark.asyncio
    async def test_test_redshift_connection_success(self):
        """Test successful connection test."""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = True

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await test_redshift_connection()

            assert 'working correctly' in result
            mock_manager.test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_redshift_connection_failure(self):
        """Test failed connection test."""
        mock_manager = Mock()
        mock_manager.test_connection.return_value = False

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await test_redshift_connection()

            assert 'failed' in result

    @pytest.mark.asyncio
    async def test_get_redshift_connection_info(self):
        """Test getting connection information."""
        mock_manager = Mock()
        mock_manager.host = 'test-host'
        mock_manager.port = 5439
        mock_manager.database = 'test_db'
        mock_manager.username = 'test_user'
        mock_manager.password = 'test_pass'
        mock_manager.cluster_identifier = None
        mock_manager.iam_profile = None

        with patch(
            'flo_ai_tools.tools.redshift_query_tool.get_redshift_connection_manager',
            return_value=mock_manager,
        ):
            result = await get_redshift_connection_info()

            assert 'test-host' in result
            assert 'test_db' in result
            assert 'test_user' in result
            assert 'Username/Password' in result


class TestToolDecorators:
    """Test that the tools are properly decorated with flo_tool."""

    def test_execute_redshift_query_has_tool_attribute(self):
        """Test that execute_redshift_query has the tool attribute."""
        assert hasattr(execute_redshift_query, 'tool')
        assert execute_redshift_query.tool is not None

    def test_execute_batch_redshift_queries_has_tool_attribute(self):
        """Test that execute_batch_redshift_queries has the tool attribute."""
        assert hasattr(execute_batch_redshift_queries, 'tool')
        assert execute_batch_redshift_queries.tool is not None

    def test_get_redshift_table_schema_has_tool_attribute(self):
        """Test that get_redshift_table_schema has the tool attribute."""
        assert hasattr(get_redshift_table_schema, 'tool')
        assert get_redshift_table_schema.tool is not None

    def test_list_redshift_tables_has_tool_attribute(self):
        """Test that list_redshift_tables has the tool attribute."""
        assert hasattr(list_redshift_tables, 'tool')
        assert list_redshift_tables.tool is not None

    def test_get_redshift_table_info_has_tool_attribute(self):
        """Test that get_redshift_table_info has the tool attribute."""
        assert hasattr(get_redshift_table_info, 'tool')
        assert get_redshift_table_info.tool is not None

    def test_test_redshift_connection_has_tool_attribute(self):
        """Test that test_redshift_connection has the tool attribute."""
        assert hasattr(test_redshift_connection, 'tool')
        assert test_redshift_connection.tool is not None

    def test_get_redshift_connection_info_has_tool_attribute(self):
        """Test that get_redshift_connection_info has the tool attribute."""
        assert hasattr(get_redshift_connection_info, 'tool')
        assert get_redshift_connection_info.tool is not None


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
