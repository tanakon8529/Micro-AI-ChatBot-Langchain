# utilities/llm/aws_bedrock_claude.py
import logging
import json
import boto3
from typing import Any, List
from langchain.llms.base import LLM
from langchain.schema import Generation, LLMResult
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import PrivateAttr

from settings.configs import MAX_TOKENS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AWSBedrockClaude(LLM):
    """
    Custom LangChain LLM wrapper for Anthropic's Claude via AWS Bedrock.
    """

    _client: Any = PrivateAttr()
    _model_id: str = PrivateAttr()
    _max_tokens: int = PrivateAttr()

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str, model_id: str):
        super().__init__()
        self._model_id = model_id
        self._max_tokens = MAX_TOKENS
        self._client = self.get_bedrock_client(aws_access_key_id, aws_secret_access_key, region_name)
        if not self._client:
            raise ValueError("Failed to initialize AWS Bedrock client")

    def get_bedrock_client(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str):
        try:
            client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            return client
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {e}")
            return None

    @property
    def _llm_type(self) -> str:
        return "aws_bedrock_claude"

    def _call(self, prompt: str, stop: List[str] = None, **kwargs: Any) -> str:
        try:
            # Prepare the request body as a JSON-encoded string
            body = json.dumps({
                "max_tokens": self._max_tokens,
                "temperature": kwargs.get("temperature", 0.3),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "anthropic_version": "bedrock-2023-05-31"
            }).encode("utf-8")

            response = self._client.invoke_model(
                modelId=self._model_id,
                contentType='application/json',
                accept='application/json',
                body=body
            )

            response_body = response['body'].read().decode('utf-8')
            response_json = json.loads(response_body)
            # Extract the generated text from the 'content' field
            generated_text = ''.join(item.get('text', '') for item in response_json.get('content', []))
            return generated_text
        except Exception as e:
            raise ValueError(f"Error calling AWS Bedrock Claude: {e}")

    def _generate(self, prompts: List[str], stop: List[str] = None, **kwargs: Any) -> LLMResult:
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop=stop, **kwargs)
            gen = Generation(text=text)
            generations.append([gen])  # Each prompt can have multiple generations
        return LLMResult(generations=generations)