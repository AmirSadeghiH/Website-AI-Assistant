from rag.rag_agent import RAGAgent
from rag.retriever import Retriever
from rag.llm_wrapper import DEFAULT_MODEL, OpenRouterLLM

import sys
import io

# تنظیم encoding برای خروجی و ورودی
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')


USER_PROMPT = (
    "از متن‌های زیر برای پاسخ دقیق به سؤال استفاده کن. "
    "اگر پاسخ در متن‌ها نبود، صادقانه بگو که اطلاعات کافی وجود ندارد. "
    "در پایان هر پاسخ، از کاربر بپرس آیا سؤال دیگری دارد یا می‌خواهد ادامه دهد."
)

SYSTEM_PROMPT = (
    "شما یک دستیار فارسی هستید که پاسخ‌ها را "
    "به صورت خلاصه اما دقیق ارائه می‌دهد."
)


class RAGService:
    def __init__(self, config=None):
        self.retriever = Retriever()

        self.llm = OpenRouterLLM(model=DEFAULT_MODEL, system_prompt=SYSTEM_PROMPT)

        self.agent = RAGAgent(
            retriever=self.retriever,
            llm=self.llm,
            user_prompt=USER_PROMPT,
        )
        self.apply_config(config)

    def apply_config(self, config=None):
        """Apply the single-site settings without rebuilding the retriever."""
        model_name = getattr(config, "model_name", "") if config else ""
        temperature = getattr(config, "temperature", None) if config else None
        system_prompt = getattr(config, "system_prompt", "") if config else ""
        user_prompt = getattr(config, "user_prompt", "") if config else ""

        self.llm.model = (model_name or DEFAULT_MODEL).strip()
        if temperature is not None:
            self.llm.temperature = float(temperature)
        self.llm.system_prompt = system_prompt.strip() or SYSTEM_PROMPT
        self.agent.user_prompt = user_prompt.strip() or USER_PROMPT
        print(
            f"[RAG] Configured LLM model={self.llm.model!r} "
            f"temperature={self.llm.temperature}",
            flush=True,
        )

    def ask(self, question: str, history=None) -> str:
        # RAGAgent performs retrieval and passes the selected context to the LLM.
        # Avoid retrieving the same query twice for every chat request.
        answer = self.agent.answer(question, history=history)
        print("LLM answer:", answer)
        return answer
