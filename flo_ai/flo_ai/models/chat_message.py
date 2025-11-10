import base64
from typing import Literal, List
from typing import Optional, Dict, Any


class MediaMessageContent:
    type: Literal['text', 'image', 'document']
    url: str | None = None
    base64: str | None = None
    mime_type: str | None = None

class ImageMessageContent(MediaMessageContent):
    def __init__(self, url: str|None = None, base64: str | None = None, mime_type: str | None = None):
        self.type = 'image'
        self.url = url
        self.base64 = base64
        self.mime_type = mime_type

class DocumentMessageContent(MediaMessageContent):
    def __init__(self, url: str | None = None, base64: str | None = None, mime_type: str | None = None):
        self.type = 'document'
        self.url = url
        self.base64 = base64
        self.mime_type = mime_type

class TextMessageContent(MediaMessageContent):
    def __init__(self, type: Literal['text'], text: str):
        self.type = 'text'
        self.text = text

class InputMessage:
    def __init__(self, role: Literal['system', 'user', 'assistant'], content: str | ImageMessageContent | DocumentMessageContent | TextMessageContent, metadata: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.metadata = metadata
class SystemMessage(InputMessage):
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('system', content, metadata)

class UserMessage(InputMessage):
    def __init__(self, content: str | ImageMessageContent | DocumentMessageContent | TextMessageContent, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('user', content, metadata)

class AssistantMessage(InputMessage):
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__('assistant', content, metadata)