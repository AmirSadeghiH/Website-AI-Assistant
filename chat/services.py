from rag.rag_agent import RAGAgent
from rag.retriever import Retriever
from rag.llm_wrapper import OpenRouterLLM

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

        self.llm = OpenRouterLLM(model="deepseek-v4-pro", system_prompt=SYSTEM_PROMPT,)

        self.agent = RAGAgent(retriever=self.retriever ,llm=self.llm, user_prompt=USER_PROMPT,)

    def ask(self, question: str) -> str:


        results = self.retriever.retrieve(question, top_k=5)
        print("Retrieved chunks scores:", [r['score'] for r in results])
        print("Text snippets:", [r['text'][:100] for r in results])

        # Call agent.answer once and reuse the result to avoid double API calls/side effects
        answer = self.agent.answer(question)
        print("LLM answer:", answer)
        return answer
        