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

class OpenRouterLLM:
    def __init__(
        self,
        api_key: str = API_KEY,
        model: str = "deepseek-v4-pro",
        base_url: str = "https://api.gapgpt.app/v1",
        temperature: float = 0.6,
        max_tokens: int = 1024,
        summary: bool = True,
        system_prompt = "شما یک دستیار فارسی هستید که پاسخ‌ها را به صورت خلاصه اما دقیق ارائه می‌دهد.",
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60
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
