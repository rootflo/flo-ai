import asyncio
from flo_ai.llm.vllm_openai import vLLMOpenAI
import time


async def example_simple_llm_call():
    llm = vLLMOpenAI(model='microsoft/phi-4', base_url='http://127.0.0.1:8080/v1')
    start_time = time.time()
    response = await llm.generate(
        messages=[{'role': 'user', 'content': 'Hello, how are you?'}]
    )
    end_time = time.time()
    print(f'Time taken: {end_time - start_time} seconds')
    print(response)


if __name__ == '__main__':
    asyncio.run(example_simple_llm_call())
