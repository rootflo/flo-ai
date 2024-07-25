from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.embeddings import Embeddings
from pymongo import MongoClient

from flo.retrievers.flo_retriever import FloRetriever

class MongoDBRetriever(FloRetriever):
    def __init__(self, 
                 dburl: str,
                 db_name: str,
                 collection: str,
                 embedding_key: str, 
                 index_name: str,
                 embedding: Embeddings) -> None:
        connection_timeout = 60000
        mongo_client = MongoClient(dburl, connectTimeoutMS=connection_timeout, socketTimeoutMS=connection_timeout)
        mongo_embedding_collection = (mongo_client
                                .get_database(db_name)
                                .get_collection(collection))
        super().__init__(MongoDBAtlasVectorSearch(
            collection=mongo_embedding_collection,
            embedding_key=embedding_key,
            embedding=embedding,
            index_name=index_name,
        ))