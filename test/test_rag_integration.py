from rag.rag_agent import RAGAgent
from rag.retriever import Retriever
from rag.llm_wrapper import OpenRouterLLM
from rag.llm_wrapper import OpenRouterLLM


USER_PROMPT = (
    "از متن‌های زیر برای پاسخ دقیق به سؤال استفاده کن. "
    "اگر پاسخ در متن‌ها نبود، صادقانه بگو که اطلاعات کافی وجود ندارد. "
    "در پایان هر پاسخ، از کاربر بپرس آیا سؤال دیگری دارد یا می‌خواهد ادامه دهد."
)

SYSTEM_PROMPT = (
    "شما یک دستیار فارسی هستید که پاسخ‌ها را "
    "به صورت خلاصه اما دقیق ارائه می‌دهد."
)


def main():
    print("\n[1] Initializing Retriever...")

    retriever = Retriever()

    print("[2] Initializing LLM...")

    llm = OpenRouterLLM(
        model="deepseek-v4-flash",
        system_prompt=SYSTEM_PROMPT,
    )

    print("[3] Initializing RAG Agent...")

    agent = RAGAgent(
        retriever=retriever,
        llm=llm,
        user_prompt=USER_PROMPT,
    )

    print("[4] Asking question...\n")

    question = "ثبت‌نام دانشجوی مهمان"

    answer = agent.answer(question)

    print("QUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)

    print("\n[OK] RAG integration test completed.")


if __name__ == "__main__":
    main()