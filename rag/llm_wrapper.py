import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

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
        max_retries: int | None = None,
        system_prompt="",
    ):
        # Retries default to 0 for the interactive chat path: a bounded,
        # predictable latency matters more than a second attempt when the
        # widget already surfaces a friendly retry message.
        request_timeout = timeout if timeout is not None else float(
            os.getenv("LLM_TIMEOUT_SECONDS", "30")
        )
        retries = max_retries if max_retries is not None else int(
            os.getenv("LLM_MAX_RETRIES", "0")
        )
        # Client is created lazily on first use so an empty corpus (fresh
        # install with no keys configured yet) never needs a provider.
        self._client = None
        self._client_options = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": request_timeout,
            "max_retries": retries,
        }
        self.model = model
        self.temperature = min(1.0, max(0.0, float(temperature)))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "700"))
        self.summary = summary
        self.system_prompt = system_prompt

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(**self._client_options)
        return self._client

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

    def stream_generate(self, prompt: str, chunk_size: int = 24):
        """Yield the answer in small text chunks (SSE-friendly).

        Uses the OpenAI-compatible streaming API. Text is buffered into
        ``chunk_size``-character groups so a widget does not re-render for
        every single token. Raises the same errors as ``generate`` — the
        streaming view converts them into SSE error events.
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt[:8000]},
                {"role": "user", "content": prompt[:16000]},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        buffer = ""
        emitted = False
        try:
            for event in stream:
                choice = event.choices[0] if getattr(event, "choices", None) else None
                delta = getattr(choice, "delta", None) if choice else None
                piece = getattr(delta, "content", None) if delta else None
                if not piece:
                    continue
                emitted = True
                buffer += str(piece)
                while len(buffer) >= chunk_size:
                    yield buffer[:chunk_size]
                    buffer = buffer[chunk_size:]
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                try:
                    close()
                except Exception:
                    pass
        if buffer:
            yield buffer
        if not emitted:
            raise RuntimeError("LLM returned an empty response.")
