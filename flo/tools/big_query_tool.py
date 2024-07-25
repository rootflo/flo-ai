from typing import Type, Optional
from google.cloud import bigquery
from langchain.tools import BaseTool
from langchain_core.tools import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain.pydantic_v1 import Field, BaseModel


class BigQueryToolInput(BaseModel):
    query: str = Field(description="""
                                  The sql query to be run on the BigQuery dataset as string and nothing else
                                  """)
    
    
class BigQueryExecutorTool(BaseTool):
    name = "BigQueryReaderTool"
    description = "A tool that can run SQL queries on BigQuery Tables, just pass query to be run as input and nothing else"
    args_schema: Type[BaseModel] = BigQueryToolInput

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return self.bigquery_executor(query)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
    def bigquery_executor(self, sql_query_string: str) -> str:
            """Executes a BigQuery SQL query and returns formatted results."""
            try:
                query = sql_query_string.replace("```sql", "").replace("```", "")
                client = bigquery.Client(project="aesy-330511")
                query_job = client.query(query)
                results = query_job.result()
                result_str = "Query Results:\n"
                for row in results:
                    result_str += f" - {row}\n"
                return result_str
            except Exception as e:
                return f"Failed to run query: {str(e)}"