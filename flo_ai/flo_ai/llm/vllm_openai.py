from flo_ai.llm.openai_llm import OpenAI


class vLLMOpenAI(OpenAI):
    def __init__(self, base_url: str = None, api_key: str = '', *args, **kwargs):
        base_url = base_url or 'http://127.0.0.1:8080/v1'
        super().__init__(base_url=base_url, api_key=api_key, *args, **kwargs)
        self.base_url = base_url
        self.api_key = api_key

    async def generate(self, *args, **kwargs):
        return await super().generate(*args, **kwargs)
