from rag.retriever import Retriever


def main():
    retriever = Retriever()

    question = "آیا می توانم به نام شرکت ای ارگان حساب باز کنم؟"

    print("\nQUESTION:")
    print(question)

    results = retriever.retrieve(
        question,
        top_k=10,
    )

    print(f"\nRESULT COUNT: {len(results)}")

    for i, result in enumerate(results, start=1):
        print("\n" + "=" * 80)
        print(f"RESULT #{i}")
        print(f"SCORE: {result['score']:.4f}")
        print(f"METADATA: {result['metadata']}")
        print("\nTEXT:")
        print(result["text"])


if __name__ == "__main__":
    main()