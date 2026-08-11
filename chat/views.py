from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .services import RAGService

rag_service = RAGService()

@csrf_exempt
@require_POST
def chat(request):
    # Robustly decode body according to request.encoding or fall back to utf-8
    raw = request.body
    try:
        body_text = raw.decode(request.encoding or 'utf-8')
    except Exception:
        # defensively replace invalid bytes instead of raising
        body_text = raw.decode('utf-8', errors='replace')

    try:
        data = json.loads(body_text)

    except json.JSONDecodeError:
        # Debug: log raw bytes and decoded preview to help diagnose encoding issues
        print("[DEBUG] Failed to parse JSON. Raw bytes preview:", raw[:200])
        print("[DEBUG] Decoded body preview:", body_text[:400])
        return JsonResponse(
            {"error": "invalid JSON."},
             status=400
        )

    message = data.get("message", "").strip()       

    if not message:
        return JsonResponse(
            {"error": "message is required."},
            status=400
        )


    try:
        answer = rag_service.ask(message)

    except Exception as exc:
        # Print exception for debugging (in production consider logging instead)
        import traceback
        tb = traceback.format_exc()
        print("[ERROR] Exception while answering:", repr(exc))
        # Also append the full traceback to a file for environments where stdout isn't visible
        try:
            with open(r'D:\ai-support-platform\error_tracebacks.log', 'a', encoding='utf-8') as fh:
                fh.write('---\n')
                fh.write(tb)
                fh.write('\n')
                fh.flush()
            print("[ERROR] Traceback written to D:\\ai-support-platform\\error_tracebacks.log")
        except Exception as write_exc:
            print("[ERROR] Failed to write traceback to file:", repr(write_exc))

        return JsonResponse(
            {"error": "An internal error occurred !"},
            status=500,
        )

    return JsonResponse({
        "answer": answer,
    })