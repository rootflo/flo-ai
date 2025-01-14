from langchain_openai import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from flo_ai.callbacks import FloExecutionLogger
from flo_ai.storage.data_collector import JSONLFileCollector, TOOLFileCollector
import os
from flo_ai import Flo, FloSession
from flo_ai.models.flo_agent import FloAgent
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain_community.tools import TavilySearchResults



# Create the LLM object
llm = AzureChatOpenAI(
    azure_endpoint="https://rootflo-useast.openai.azure.com",
    model_name="gpt-4o-mini",
    temperature=0.2,
    api_version="2023-03-15-preview",
    api_key="e60604bc2c64428c947ea3d83025b0a4",
)
file_collector = JSONLFileCollector("./temp.jsonl")

tool_collector = TOOLFileCollector('./tools.jsonl')

# Create a tool logger with the collector
local_tracker = FloExecutionLogger(file_collector, tool_collector)

prompt = PromptTemplate.from_template("1 + {number} = ")

chain = LLMChain(llm=llm,prompt=prompt,callbacks=[local_tracker])
print(chain.invoke({"number":2}))







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
print(agent_flo.invoke("Whats the whether in Aroor kochi, India ?"))


