from flo_ai import Flo
from flo_ai import FloSession
from langchain_openai import ChatOpenAI
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from dotenv import load_dotenv
load_dotenv()

llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo')

session = FloSession(
    llm, 
    log_level="ERROR"
)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
tool = WikipediaQueryRun(api_wrapper=api_wrapper)

session.register_tool(
    name="WikipediaAPIWrapper", 
    tool=tool
)

simple_weather_checking_agent = """
apiVersion: flo/alpha-v1
kind: FloAgent
name: weather-assistant
agent:
    name: WeatherAssistant
    kind: agentic
    job: >
      Answer question based on user question
    tools:
      - name: WikipediaAPIWrapper
"""

from IPython.display import Image, display
flo = Flo.build(session, simple_weather_checking_agent, log_level="ERROR")

result = flo.invoke("What is Leo DiCaprio's middle name?\n\nAction: Wikipedia")
print(result)