import json
import logging
import traceback
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

_rag_service = None
ERROR_LOG = Path(settings.BASE_DIR) / 'error_tracebacks.log'
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
MAX_HISTORY_ITEMS = 8
MAX_HISTORY_CONTENT_LENGTH = 2000


def get_rag_service():
    global _rag_service
    if _rag_service is None:
        from .services import RAGService
        _rag_service = RAGService()
    return _rag_service


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "ai-support-platform"})


@csrf_exempt
@require_POST
def chat(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "invalid_json", "message": "Request body must be valid JSON."},
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {"error": "invalid_payload", "message": "Request body must be a JSON object."},
            status=400,
        )

    message = data.get("message", "")
    if not isinstance(message, str):
        return JsonResponse(
            {"error": "invalid_message", "message": "The message must be a string."},
            status=400,
        )
    message = message.strip()

    if not message:
        return JsonResponse(
            {"error": "message_required", "message": "The message is required."},
            status=400,
        )

    if len(message) > MAX_MESSAGE_LENGTH:
        return JsonResponse(
            {
                "error": "message_too_long",
                "message": f"The message must be {MAX_MESSAGE_LENGTH} characters or fewer.",
            },
            status=413,
        )

    history = data.get("history", [])
    if history is None:
        history = []
    if not isinstance(history, list):
        return JsonResponse(
            {"error": "invalid_history", "message": "History must be a JSON list."},
            status=400,
        )
    normalized_history = []
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        normalized_history.append({
            "role": role,
            "content": content.strip()[:MAX_HISTORY_CONTENT_LENGTH],
        })

    try:
        answer = get_rag_service().ask(message, history=normalized_history)
    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception("Exception while answering chat request: %s", exc)
        try:
            with open(ERROR_LOG, 'a', encoding='utf-8') as fh:
                fh.write('---\n')
                fh.write(tb)
                fh.write('\n')
        except OSError:
            pass
        error_payload = {
            "error": "backend_error",
            "message": "The assistant is temporarily unavailable.",
        }
        if settings.DEBUG:
            error_payload["detail"] = str(exc)
        return JsonResponse(
            error_payload,
            status=500,
        )

    return JsonResponse({"answer": str(answer)})
