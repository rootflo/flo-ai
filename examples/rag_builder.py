from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
import os
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
load_dotenv()

from flo_ai import FloSession
from flo_ai.retrievers.flo_retriever import FloRagBuilder

db_url = os.getenv("MONGO_DB_URL")

connection_timeout = 60000
mongo_client = MongoClient(db_url, connectTimeoutMS=connection_timeout, socketTimeoutMS=connection_timeout)
mongo_embedding_collection = (mongo_client
                        .get_database("dohabank")
                        .get_collection("products"))

store = MongoDBAtlasVectorSearch(
    collection=mongo_embedding_collection,
    embedding_key="embedding",
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    index_name="bank-products-index",
)


llm = ChatOpenAI(temperature=0, model_name='gpt-4o')
session = FloSession(llm)
rag_builder = FloRagBuilder(session,
               store.as_retriever())
bank_context = """
You are the co-pilot for a relationship manager at Doha Bank, assisting in selling the bank's products. Talk like you are an expert on the financial products offered by the bank.
If the currency is not mentioned in the text, then assume the currency to be: "QED"
"""
    
qa_shop_context_prompt = """
1. Speak as a support bot, addressing the customer in the third person.
2. Example: "Please request the customer to provide the following documents to apply for a loan."
3. Answer questions in a list format whenever possible.

Always talk authoritatively about the information that you have, you are given all the information that is avaiable with the banks documents are context.
Do not answer, if you dont have any information about it, just say "Sorry, I don't have enough information to answer your question at the moment."
"""

# qa_system_prompt = get_qa_system_prompt()

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", bank_context + "\n" + qa_shop_context_prompt),
        # ("system", qa_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
    ]
)
rag = rag_builder.add_history_awareness().build(qa_prompt)
print(rag.invoke({"question": "Tell me about corporate loans", "chat_history": []}))

