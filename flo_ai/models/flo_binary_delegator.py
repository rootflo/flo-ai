from langchain.agents import AgentExecutor
from langchain_core.runnables import Runnable
from typing import Union, Optional
from langchain_core.prompts import ChatPromptTemplate
from flo_ai.state.flo_session import FloSession
from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class BinaryDelegator():

    def __init__(self,
                 session: FloSession,
                 executor: Runnable,
                 name: str
                 ) -> None:
        self.session = session
        self.executor = executor
        self.name = name
        

    class Builder():

        def __init__(self, 
                    session: FloSession,
                    name: str, 
                    prompt: Union[ChatPromptTemplate, str],
                    llm: Union[BaseLanguageModel, None] =  None) -> None:
            
            self.session = session
            self.name = name
            self.prompt = PromptTemplate(
                template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
                Here are the facts:
                \n ------- \n
                {facts} 
                \n ------- \n
                Here is the answer: {generation}
                Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. \n
                Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.""",
                input_variables=["generation", "documents"],
            )

        def build(self):
            chain = self.prompt | self.session.llm | JsonOutputParser()
            return BinaryDelegator(session=self.session, executor=chain, name=self.name)