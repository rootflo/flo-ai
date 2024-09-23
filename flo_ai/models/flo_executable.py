from flo_ai.models.flo_member import FloMember
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from enum import Enum
from flo_ai.state.flo_state import STATE_NAME_MESSAGES

class ExecutableType(Enum):
    agentic = "agentic"
    llm = "llm"
    tool = "tool" 
    reflection = "reflection"
    delegator = "delegator"

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
            STATE_NAME_MESSAGES: [
                HumanMessage(content=work)
            ]
        }, config)
    
    def invoke(self, work, config = None):
        return self.runnable.invoke({
             STATE_NAME_MESSAGES: [
                HumanMessage(content=work)
            ], 
        }, config)
    

    def draw(self, xray=True):
        return self.runnable.get_graph().draw_mermaid_png()