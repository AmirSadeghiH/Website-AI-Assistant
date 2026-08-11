import sys
import traceback

sys.path.append(r"D:\ai-support-platform")

from chat.services import RAGService

svc = RAGService()

try:
    print(svc.ask("سلام، چگونه می‌توانم حساب باز کنم؟"))
except Exception:
    traceback.print_exc()
