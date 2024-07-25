from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from flo.tools.big_query_tool import BigQueryExecutorTool

TAVILY_WEB_SEARCH = "TavilySearchResults"
DUCK_DUCK_GO_SEARCH = "DuckDuckGoSearchRun"
BIG_QUERY_EXECUTOR = "BigQueryExecutor"

yaml_supported_tool_names = [
    TAVILY_WEB_SEARCH,
    DUCK_DUCK_GO_SEARCH
]

yaml_tool_map = {
    TAVILY_WEB_SEARCH: TavilySearchResults,
    DUCK_DUCK_GO_SEARCH: DuckDuckGoSearchRun,
    BIG_QUERY_EXECUTOR: BigQueryExecutorTool
}