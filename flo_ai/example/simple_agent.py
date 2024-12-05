from flo_ai import Flo
from flo_ai import FloSession
from flo_ai.storage.file_data_collector import FileDataCollector
from flo_ai.storage.data_collector import LLMData, AgentData
from flo_ai.callbacks.flo_callbacks import FloCallback, FloCallbackResponse
from langchain_openai import AzureChatOpenAI
from langchain_community.tools.tavily_search.tool import TavilySearchResults
import os
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

llm = AzureChatOpenAI(
    temperature=0,
    deployment_name="gpt-4",  
    model_name="gpt-4",       
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),  
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview"
)

data_collector = FileDataCollector(storage_dir="flo_storage")

def file_storage_callback_handler(response: FloCallbackResponse):
    timestamp = datetime.now()
    try:
        if response.type == 'on_tool_end':
            llm_data = LLMData(
                session_id=response.name,
                timestamp=timestamp,
                model_name=response.model_name or "unknown",
                input_text=str(response.input),  
                output_text=str(response.output), 
                tokens_used=response.args.get('tokens_used', 0),
                latency_ms=response.args.get('latency_ms', 0),
                metadata=dict(response.args) 
            )
            data_collector.store_llm_interaction(llm_data)
        
        elif response.type == 'on_agent_end':
            agent_data = AgentData(
                session_id=response.name,
                timestamp=timestamp,
                agent_name=response.name,
                agent_type="agentic",
                input_data=str(response.input),  
                output_data=str(response.output),  
                metadata={
                    'model_name': response.model_name,
                    **dict(response.args) 
                }
            )
            data_collector.store_agent_interaction(agent_data)
    except Exception as e:
        print(f"Error in callback handler: {str(e)}")

callback = FloCallback(file_storage_callback_handler)

session = FloSession(
    llm, 
    log_level="ERROR",
    data_collector=data_collector
)

session.register_tool(
    name="InternetSearchTool", 
    tool=TavilySearchResults()
)

session.register_callback(callback=callback)

simple_weather_checking_agent = """
apiVersion: flo/alpha-v1
kind: FloAgent
name: weather-assistant
agent:
    name: WeatherAssistant
    kind: agentic
    job: >
      Given the city name you are capable of answering the latest whether this time of the year by searching the internet
    tools:
      - name: InternetSearchTool
"""

flo = Flo.build(session, simple_weather_checking_agent, log_level="ERROR")

result = flo.invoke("What's the weather in New Delhi, India?")

session_data = data_collector.get_session_data(session.session_id)
print("\nStored Session Data:")
print(json.dumps(session_data, indent=2))