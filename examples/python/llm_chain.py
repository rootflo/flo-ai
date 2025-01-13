from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from flo_ai.storage.data_collector import JSONLFileCollector
from flo_ai.callbacks import FloExecutionLogger
from langchain.chains import LLMChain

prompt_template = "Tell me a {adjective} joke"
prompt = PromptTemplate(
    input_variables=["adjective"], template=prompt_template
)
llm = AzureChatOpenAI(
    azure_endpoint="https://rootflo-useast.openai.azure.com",
    model_name="gpt-4o-mini",
    temperature=0.2,
    api_version="2023-03-15-preview",
    api_key="e60604bc2c64428c947ea3d83025b0a4",
)
file_collector = JSONLFileCollector("./temp.jsonl")

# Create a tool logger with the collector
local_tracker = FloExecutionLogger(file_collector)

chain = LLMChain(llm=llm,prompt=prompt,callbacks=[local_tracker])

print(chain.invoke("your adjective here"))