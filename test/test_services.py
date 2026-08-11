from chat.services import RAGService

def main():
    print("[1] Creating RAG service...")

    service = RAGService()

    print("[2] Asking question...\n")

    question = "هزینه دریافت کارت چقدر است؟"

    answer = service.ask(question)

    print("QUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)

    print("\n[OK] Service test completed.")


if __name__ == "__main__":
    main()