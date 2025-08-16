from typing import Optional
from google import genai
from flo_ai.llm.gemini_llm import GeminiLLM


class VertexAI(GeminiLLM):
    def __init__(
        self,
        model: str = 'gemini-2.5-flash',
        temperature: float = 0.7,
        api_key: Optional[str] = None,
        base_url: str = None,
        project: str = None,
        location: str = None,
        **kwargs,
    ):
        super().__init__(model, api_key, temperature, **kwargs)
        self.client = genai.Client(project=project, location=location, vertexai=True)
