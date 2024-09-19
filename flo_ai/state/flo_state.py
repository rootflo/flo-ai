from typing import Annotated, List, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from typing import List, Tuple, Annotated, TypedDict, Dict

import operator

# The agent state is the input to each node in the graph
class TeamFloAgentState(TypedDict):
    # The annotation tells the graph that new messages will always
    # be added to the current states
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # The 'next' field indicates where to route to next
    next: str
    reflection_messages: Annotated[Sequence[BaseMessage], operator.add]

class TeamFloAgentStateWithPlan(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str