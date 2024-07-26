from langchain_core.vectorstores import VectorStore

class FloRetriever():
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store
        self.retriver = self.vector_store.as_retriever()