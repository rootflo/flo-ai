from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from flo_ai.storage.data_collector import JSONLFileCollector, TOOLFileCollector
from flo_ai.callbacks import FloExecutionLogger
from langchain.chains import LLMChain
import os
from flo_ai import Flo, FloSession
from flo_ai.models.flo_agent import FloAgent
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain_community.tools import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()


prompt_template = "Tell me a {adjective} joke"
prompt = PromptTemplate(
    input_variables=["adjective"], template=prompt_template
)

file_collector = JSONLFileCollector("./logger.jsonl")
tool_collector = TOOLFileCollector('./tools.jsonl')

# Create a tool logger with the collector
local_tracker = FloExecutionLogger(file_collector, tool_collector)

llm = AzureChatOpenAI(
    azure_endpoint="https://rootflo-useast.openai.azure.com",
    model_name="gpt-4o-mini",
    temperature=0.2,
    api_version="2023-03-15-preview",
    api_key="e60604bc2c64428c947ea3d83025b0a4",
    callbacks=[local_tracker]
)


chain = LLMChain(llm=llm,prompt=prompt,callbacks=[local_tracker])

print(chain.invoke({"adjective": "funny"}))

session = FloSession(llm)
session.register_callback(local_tracker)

os.environ["TAVILY_API_KEY"] = "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"
tavily_tool = TavilySearchResults()

session.register_tool("thappal",tavily_tool)


weather_agent = FloAgent.create(
    session=session,
    name="Blogger",
    job="You can research the internet and create a blog about the topic given by the user",
    tools=[tavily_tool]
)


agent_flo: Flo = Flo.create(session, weather_agent)
# print("\n\n agent_flo",agent_flo.runnable)
print(agent_flo.invoke("Whats the whether in New Delhi, India ?"))