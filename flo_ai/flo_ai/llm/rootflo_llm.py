from enum import Enum
from typing import AsyncIterator, Dict, Any, List, Optional
from datetime import datetime, timedelta
import jwt
from .base_llm import BaseLLM, ImageMessage
from .openai_llm import OpenAI
from .gemini_llm import Gemini
from .anthropic_llm import Anthropic
from flo_ai.tool.base_tool import Tool


class LLMProvider(Enum):
    """Enum for supported LLM providers"""

    OPENAI = 'openai'
    GEMINI = 'gemini'
    ANTHROPIC = 'anthropic'


class RootFloLLM(BaseLLM):
    """
    Proxy LLM class that routes to different SDK implementations based on type.
    Acts as a unified interface to OpenAI, Gemini, and Anthropic SDKs via a proxy URL.
    """

    def __init__(
        self,
        base_url: str,
        model_id: str,
        llm_model: str,
        llm_provider: LLMProvider,
        app_key: str,
        app_secret: str,
        issuer: str,
        audience: str,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Initialize RootFloLLM proxy.

        Args:
            base_url: The base URL of the proxy server
            model_id: The model identifier
            llm_provider: Type of LLM SDK to use (LLMProvider enum)
            app_key: Application key for X-Rootflo-Key header
            app_secret: Application secret for JWT signing
            issuer: JWT issuer claim
            audience: JWT audience claim
            temperature: Temperature parameter for generation
            **kwargs: Additional parameters to pass to the underlying SDK
        """
        # Generate JWT token
        now = datetime.now()
        payload = {
            'iss': issuer,
            'aud': audience,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=3600)).timestamp()),
            'role_id': 'floconsole-service',
            'user_id': 'service',
            'service_auth': True,
        }
        service_token = jwt.encode(payload, app_secret, algorithm='HS256')
        api_token = f'fc_{service_token}'

        super().__init__(
            model=llm_model, api_key=api_token, temperature=temperature, **kwargs
        )

        self.base_url = base_url
        self.model_id = model_id
        self.llm_provider = llm_provider

        # Construct full URL
        full_url = f'{base_url}/{model_id}'

        # Prepare custom headers for proxy authentication
        custom_headers = {'X-Rootflo-Key': app_key}

        # Instantiate appropriate SDK wrapper based on llm_provider
        if llm_provider == LLMProvider.OPENAI:
            self._llm = OpenAI(
                model=llm_model,
                base_url=full_url,
                api_key=api_token,
                temperature=temperature,
                custom_headers=custom_headers,
                **kwargs,
            )
        elif llm_provider == LLMProvider.ANTHROPIC:
            self._llm = Anthropic(
                model=llm_model,
                base_url=full_url,
                api_key=api_token,
                temperature=temperature,
                custom_headers=custom_headers,
                **kwargs,
            )
        elif llm_provider == LLMProvider.GEMINI:
            # Gemini SDK - pass base_url which will be handled via http_options
            self._llm = Gemini(
                model=llm_model,
                api_key=api_token,
                temperature=temperature,
                base_url=full_url,
                custom_headers=custom_headers,
                **kwargs,
            )
        else:
            raise ValueError(f'Unsupported LLM provider: {llm_provider}')

    async def generate(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        return await self._llm.generate(
            messages, functions=functions, output_schema=output_schema, **kwargs
        )

    async def stream(
        self,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate a streaming response from the LLM"""
        async for chunk in self._llm.stream(messages, functions=functions, **kwargs):
            yield chunk

    def get_message_content(self, response: Any) -> str:
        """Extract message content from response"""
        return self._llm.get_message_content(response)

    def format_tool_for_llm(self, tool: 'Tool') -> Dict[str, Any]:
        """Format a tool for the specific LLM's API"""
        return self._llm.format_tool_for_llm(tool)

    def format_tools_for_llm(self, tools: List['Tool']) -> List[Dict[str, Any]]:
        """Format a list of tools for the specific LLM's API"""
        return self._llm.format_tools_for_llm(tools)

    def format_image_in_message(self, image: ImageMessage) -> str:
        """Format a image in the message"""
        return self._llm.format_image_in_message(image)
