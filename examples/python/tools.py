from langchain_openai import AzureChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from flo_ai.callbacks import FloExecutionLogger
from flo_ai.storage.data_collector import JSONLFileCollector
import os
from flo_ai import Flo, FloSession
from flo_ai.models.flo_agent import FloAgent
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain_community.tools import TavilySearchResults
from pydantic import BaseModel,Field
from typing import List
from flo_ai.tools import flotool

from langchain.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import math

class AdditionToolInput(BaseModel):
    numbers: List[int] = Field(..., description='List of numbers to add')

@flotool(name='AdditionTool', description='Tool to add numbers', argument_contract=AdditionToolInput)
def addition_tool(numbers: List[int]) -> str:
    result = sum(numbers)
    return f'The sum is {result}'

@flotool(
    name='MultiplicationTool',
    description='Tool to multiply numbers to get product of numbers',
)
def mul_tool(numbers: List[int]) -> str:
    result = math.prod(numbers)
    # await asyncio.sleep(1)
    return f'The product is {result}'

# Create the LLM object
llm = AzureChatOpenAI(
    azure_endpoint="https://rootflo-useast.openai.azure.com",
    model_name="gpt-4o-mini",
    temperature=0.2,
    api_version="2023-03-15-preview",
    api_key="e60604bc2c64428c947ea3d83025b0a4",
)
file_collector = JSONLFileCollector("./temp.jsonl")

local_tracker = FloExecutionLogger(file_collector)


session = FloSession(llm)
session.register_callback(local_tracker)


session.register_tool(name='Adder', tool=addition_tool).register_tool(
    name='Multiplier', tool=mul_tool
)

add_agent = FloAgent.create(
    session=session,
    name="teacher",
    job="given three number add first two numbers and multiply with third number",
    tools=[addition_tool,mul_tool]
)


mul_flo: Flo = Flo.create(session, add_agent)
print(mul_flo.invoke("Can you add 10 and 10 and multiply by 3?"))

