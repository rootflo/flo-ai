from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain_core.runnables import Runnable
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from flo_ai.models.flo_executable import ExecutableFlo
from flo_ai.state.flo_session import FloSession
from typing import Union, Optional
from flo_ai.yaml.config import AgentConfig
from flo_ai.models.flo_executable import ExecutableType

class FloAgent(ExecutableFlo):
    def __init__(self,
                 agent: Runnable, 
                 executor: AgentExecutor, 
                 config: AgentConfig) -> None:
        super().__init__(config.name, executor, ExecutableType.agentic)
        self.agent: Runnable =  agent,
        self.executor: AgentExecutor = executor
        self.config: AgentConfig = config

    class Builder:
        def __init__(self, 
                    session: FloSession,
                    config: AgentConfig,
                    tools: list[BaseTool],
                    verbose: bool = True,
                    role: Optional[str] = None,
                    llm: Union[BaseLanguageModel, None] =  None,
                    return_intermediate_steps: bool = False,
                    handle_parsing_errors: bool = True) -> None:
            prompt: Union[ChatPromptTemplate, str] = config.job
            
            self.name: str = config.name
            self.llm = llm if llm is not None else session.llm
            self.config = config
            # TODO improve to add more context of what other agents are available
            system_prompts = [("system", "You are a {}".format(role)), ("system", prompt)] if role is not None else [("system", prompt)]
            system_prompts.append(MessagesPlaceholder(variable_name="messages"))
            system_prompts.append(MessagesPlaceholder(variable_name="agent_scratchpad"))
            self.prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
                system_prompts
            ) if isinstance(prompt, str) else prompt
            self.tools: list[BaseTool] = tools
            self.verbose = verbose
            self.return_intermediate_steps = return_intermediate_steps
            self.handle_parsing_errors = handle_parsing_errors


        def build(self) -> AgentExecutor:
            agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
            executor = AgentExecutor(agent=agent, 
                                tools=self.tools, 
                                verbose=self.verbose, 
                                return_intermediate_steps=self.return_intermediate_steps, 
                                handle_parsing_errors=self.handle_parsing_errors)
            return FloAgent(agent, executor, self.config)
