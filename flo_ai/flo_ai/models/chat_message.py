from typing import Literal
from dataclasses import dataclass
from typing import Optional, Dict, Any
from flo_ai.llm.base_llm import DocumentMessage, ImageMessage



class InputMessage:
    def __init__(self, role: Literal['system', 'user', 'assistant'], content: str | ImageMessage | DocumentMessage, metadata: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.metadata = metadata
class SystemMessage(InputMessage):
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('system', content, metadata)

class UserMessage(InputMessage):
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('user', content, metadata)

class AssistantMessage(InputMessage):
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('assistant', content, metadata)