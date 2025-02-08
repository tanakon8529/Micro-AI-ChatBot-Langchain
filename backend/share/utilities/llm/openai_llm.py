# utilities/llm/openai_llm.py
import logging
from typing import Any, List
from langchain.llms.base import LLM
from langchain.schema import Generation, LLMResult
from pydantic import PrivateAttr
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OpenAIChatLLM(LLM):
    """
    Custom LangChain LLM wrapper for OpenAI's ChatGPT using ChatOpenAI.
    """

    _client: Any = PrivateAttr()
    _model_name: str = PrivateAttr()
    _temperature: float = PrivateAttr()
    _openai_api_key: str = PrivateAttr()

    def __init__(self, openai_api_key: str, model_name: str, temperature: float = 0.7):
        super().__init__()
        self._openai_api_key = openai_api_key
        self._model_name = model_name
        self._temperature = temperature
        self._client = ChatOpenAI(
            openai_api_key=self._openai_api_key,
            model_name=self._model_name,
            temperature=self._temperature
        )

    @property
    def _llm_type(self) -> str:
        return "openai_chat_llm"

    def _call(self, prompt: str, stop: List[str] = None, **kwargs: Any) -> str:
        try:
            response = self._client.invoke(prompt, stop=stop, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"Error calling OpenAI ChatOpenAI: {e}")
            raise ValueError(f"Error calling OpenAI ChatOpenAI: {e}")

    async def _agenerate(self, prompts: List[str], stop: List[str] = None, **kwargs: Any) -> LLMResult:
        generations = []
        for prompt in prompts:
            try:
                text = await self._client.ainvoke(prompt, stop=stop, **kwargs)
                gen = Generation(text=text.content if hasattr(text, 'content') else str(text))
                generations.append([gen])
            except Exception as e:
                logger.error(f"Async error calling OpenAI ChatOpenAI: {e}")
                raise ValueError(f"Async error calling OpenAI ChatOpenAI: {e}")
        return LLMResult(generations=generations)

    def _generate(self, prompts: List[str], stop: List[str] = None, **kwargs: Any) -> LLMResult:
        generations = []
        for prompt in prompts:
            try:
                text = self._call(prompt, stop=stop, **kwargs)
                gen = Generation(text=text)
                generations.append([gen])
            except Exception as e:
                logger.error(f"Synchronous error calling OpenAI ChatOpenAI: {e}")
                raise ValueError(f"Synchronous error calling OpenAI ChatOpenAI: {e}")
        return LLMResult(generations=generations)