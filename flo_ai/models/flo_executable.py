from flo_ai.models.flo_member import FloMember
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from enum import Enum

class ExecutableType(Enum):
    agentic = "agentic"
    llm = "llm"
    tool = "tool" 
    reflexion = "reflexion"

    @staticmethod
    def isAgent(type: 'ExecutableType'):
        match(type):
            case ExecutableType.agentic:
                return True
            case ExecutableType.llm:
                return True
            case ExecutableType.tool:
                return True
        return False

class ExecutableFlo(FloMember):
    def __init__(self, 
                 name: str, 
                 runnable: Runnable, 
                 type: str = "team") -> None:
        super().__init__(name, type)
        self.runnable = runnable

    def stream(self, work, config = None):
        return self.runnable.stream({
             "messages": [
                HumanMessage(content=work)
            ]
        }, config)
    
    def invoke(self, work, config = None):
        return self.runnable.invoke({
             "messages": [
                HumanMessage(content=work)
            ]
        }, config)