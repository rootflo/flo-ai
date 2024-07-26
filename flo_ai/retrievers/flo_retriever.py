from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.runnables import RunnableParallel
from flo_ai.state.flo_session import FloSession
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class FloRagBuilder():
    def __init__(self, session: FloSession, retriever: VectorStoreRetriever) -> None:
        self.session = session
        self.retriever = retriever
    
        self.history_aware_retriever = None
        self.is_history_aware = False

    def add_history_awareness(self):
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{question}"),
            ]
        )
        self.history_aware_retriever = contextualize_q_prompt | self.session.llm | StrOutputParser()
        self.is_history_aware = True
        return self

    def __get_retriever(self):
        def __precontext_retriver(input_prompt: dict):
            if input_prompt.get("chat_history"):
                return self.history_aware_retriever
            else:
                return input_prompt["question"]
            
        if self.is_history_aware:
            return __precontext_retriver | self.retriever
        return self.retriever
    
    def __format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def build(self, rag_prompt: str):
        rag_chain = (
            RunnablePassthrough.assign(
                context=(lambda x: x["context"]),
            )
            | rag_prompt
            | self.session.llm
            
        )

        rag_chain_with_source = RunnableParallel(
            {
                "context": self.__get_retriever() | self.__format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda x: x["chat_history"]
            }
        ).assign(answer=rag_chain)

        return rag_chain_with_source
