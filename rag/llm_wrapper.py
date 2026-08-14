import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
DEFAULT_BASE_URL = (
    os.getenv("LLM_API_URL")
    or os.getenv("LLM_BASE_URL")
    or os.getenv("BASE_URL")
    or "https://api.gapgpt.app/v1"
)
DEFAULT_MODEL = os.getenv("LLM_MODEL") or os.getenv("MODEL") or "deepseek-v4-pro"


class OpenRouterLLM:
    def __init__(
        self,
        api_key: str = API_KEY,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        temperature: float = 0.6,
        max_tokens: int | None = None,
        summary: bool = True,
        timeout: float | None = None,
        system_prompt="",
    ):
        request_timeout = timeout or float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "1"))
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=request_timeout,
            max_retries=max_retries,
        )
        self.model = model
        self.temperature = min(1.0, max(0.0, float(temperature)))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "700"))
        self.summary = summary
        self.system_prompt = system_prompt

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt[:8000]},
                {"role": "user", "content": prompt[:16000]},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = getattr(response.choices[0].message, "content", None)
        if not content:
            raise RuntimeError("LLM returned an empty response.")
        return str(content).strip()[:12000]
