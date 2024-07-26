from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from flo.retrievers.flo_retriever import FloRetriever
from typing import Dict, Optional

import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

class ChromDBRetriever(FloRetriever):
    def __init__(self, 
                 collection: str,
                 embedding: Embeddings,
                 type: str = "persistent",
                 connection_args: Optional[Dict] = None) -> None:
        if type == "http":
            client = chromadb.HttpClient(**connection_args, 
                                         settings=Settings(), 
                                         tenant=DEFAULT_TENANT, 
                                         database=DEFAULT_DATABASE)
        else:
            client = chromadb.PersistentClient(
                **connection_args, 
                settings=Settings(), 
                tenant=DEFAULT_TENANT, 
                database=DEFAULT_DATABASE)
        chromdb = Chroma(
            client=client,
            collection_name=collection,
            embedding_function=embedding
        )
        super().__init__(chromdb)