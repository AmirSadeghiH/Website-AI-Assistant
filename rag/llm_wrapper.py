from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

import sys
import io

# تنظیم encoding برای خروجی و ورودی
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

API_KEY = os.getenv('LLM_API_KEY')
DEFAULT_BASE_URL = os.getenv('LLM_BASE_URL') or os.getenv('BASE_URL') or 'https://api.gapgpt.app/v1'
DEFAULT_MODEL = os.getenv('LLM_MODEL') or os.getenv('MODEL') or 'deepseek-v4-pro'

class OpenRouterLLM:
    def __init__(
        self,
        api_key: str = API_KEY,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        temperature: float = 0.6,
        max_tokens: int = 1024,
        summary: bool = True,
        timeout: float | None = None,
        system_prompt = "شما یک دستیار فارسی هستید که پاسخ‌ها را به صورت خلاصه اما دقیق ارائه می‌دهد.",
    ):
        request_timeout = timeout or float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "0"))
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=request_timeout,
            max_retries=max_retries,
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.summary = summary
        self.system_prompt = system_prompt

    def generate(self, prompt: str) -> str:
        if self.summary:
            system_content = self.system_prompt
        else:
            system_content = self.system_prompt

        # Debug: show a safe preview of the prompt (repr) to verify encoding/content
        try:
            print('[DEBUG] LLM prompt preview (repr):', repr(prompt)[:1000])
        except Exception:
            # never fail because of logging
            pass

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            print(
                f"[LLM ERROR] model={self.model!r} base_url={self.client.base_url!s} "
                f"error={exc!r}",
                flush=True,
            )
            raise

        # Robustly extract text from various possible response shapes
        try:
            content = response.choices[0].message.content
        except Exception:
            try:
                content = response.choices[0].text
            except Exception:
                # fallback to string representation (for debugging)
                content = str(response)

        try:
            print('[DEBUG] LLM response preview (repr):', repr(content)[:1000])
        except Exception:
            pass

        return content.strip()
