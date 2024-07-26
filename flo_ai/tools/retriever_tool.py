from langchain.tools.retriever import create_retriever_tool
from langchain_core.retrievers import BaseRetriever

MONGODB_RETRIVER_TOOL = "MongoDBRetreiverTool"
CHROMADB_RETRIVER_TOOL = "ChromaDBRetreiverTool"

def fetch_retriver_tool_by_name(tool_name: str, 
                                tool_description: str,
                                retriever: BaseRetriever):
    return create_retriever_tool(
        retriever,
        tool_name,
        tool_description
    )