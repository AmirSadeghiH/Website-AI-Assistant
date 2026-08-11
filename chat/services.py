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
    def __init__(self):
        self.retriever = Retriever()

        print(f"[RAG] Initializing LLM model={DEFAULT_MODEL!r}", flush=True)
        self.llm = OpenRouterLLM(model=DEFAULT_MODEL, system_prompt=SYSTEM_PROMPT,)

        self.agent = RAGAgent(retriever=self.retriever ,llm=self.llm, user_prompt=USER_PROMPT,)

    def ask(self, question: str, history=None) -> str:
        # RAGAgent performs retrieval and passes the selected context to the LLM.
        # Avoid retrieving the same query twice for every chat request.
        answer = self.agent.answer(question, history=history)
        print("LLM answer:", answer)
        return answer
