import json
import logging
import traceback
import uuid
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import AnalyticsEvent, Conversation, Message, WidgetConfig

_rag_service = None
_rag_artifact_signature = None
ERROR_LOG = Path(settings.BASE_DIR) / "error_tracebacks.log"
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
MAX_HISTORY_ITEMS = 8
MAX_HISTORY_CONTENT_LENGTH = 2000
EVENT_TYPES = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}


def get_rag_service():
    global _rag_service, _rag_artifact_signature
    config = get_widget_config()
    artifact_paths = (
        Path(settings.BASE_DIR) / "Data" / "chunks.json",
        Path(settings.BASE_DIR) / "Data" / "metadata.json",
        Path(settings.BASE_DIR) / "Data" / "embeddings.npy",
    )
    signature = tuple(
        (str(path), path.stat().st_mtime_ns if path.exists() else 0)
        for path in artifact_paths
    )
    if _rag_service is None or signature != _rag_artifact_signature:
        from .services import RAGService

        _rag_service = RAGService(config=config)
        _rag_artifact_signature = signature
    else:
        _rag_service.apply_config(config)
    return _rag_service


def get_widget_config():
    config = WidgetConfig.objects.first()
    if config is None:
        config = WidgetConfig.objects.create()
    return config


def widget_config_payload(config):
    return {
        "business_name": config.business_name,
        "website_url": config.website_url,
        "title": config.title,
        "subtitle": config.subtitle,
        "greeting": config.greeting,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "font_family": config.font_family,
        "position": config.position,
        "show_history": config.show_history,
        "allow_feedback": config.allow_feedback,
        "show_powered_by": config.show_powered_by,
        "suggestions": config.suggestions or [],
        "faq_url": config.faq_url,
        "privacy_url": config.privacy_url,
        "support_email": config.support_email,
    }


def find_or_create_conversation(external_id, request):
    external_id = (external_id or "").strip()[:100]
    if not external_id:
        external_id = f"conversation_{uuid.uuid4().hex}"
    conversation, created = Conversation.objects.get_or_create(
        external_id=external_id,
        defaults={
            "page_url": request.headers.get("Referer", "")[:1000],
            "referrer": request.headers.get("Origin", "")[:1000],
            "user_agent": request.headers.get("User-Agent", "")[:1000],
        },
    )
    if created:
        AnalyticsEvent.objects.create(
            conversation=conversation,
            event_type="conversation_started",
            path=request.headers.get("Referer", "")[:1000],
        )
    return conversation


def record_event(event_type, request, conversation=None, metadata=None):
    if event_type not in EVENT_TYPES:
        return
    AnalyticsEvent.objects.create(
        conversation=conversation,
        event_type=event_type,
        path=request.headers.get("Referer", "")[:1000],
        metadata=metadata or {},
    )


def parse_json_body(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse(
            {"error": "invalid_json", "message": "Request body must be valid JSON."},
            status=400,
        )
    if not isinstance(data, dict):
        return None, JsonResponse(
            {"error": "invalid_payload", "message": "Request body must be a JSON object."},
            status=400,
        )
    return data, None


def normalize_history(history):
    if history is None:
        history = []
    if not isinstance(history, list):
        return None
    normalized = []
    for item in history[-MAX_HISTORY_ITEMS:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        normalized.append({
            "role": role,
            "content": content.strip()[:MAX_HISTORY_CONTENT_LENGTH],
        })
    return normalized


@require_GET
def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "ai-support-platform",
        "mode": "single-site",
    })


@require_GET
def widget_config(request):
    return JsonResponse(widget_config_payload(get_widget_config()))


@require_GET
def conversation_history(request):
    external_id = (request.GET.get("conversation_id") or "").strip()[:100]
    if not external_id:
        return JsonResponse({"messages": []})
    conversation = Conversation.objects.filter(external_id=external_id).first()
    if conversation is None:
        return JsonResponse({"messages": []})
    messages = list(
        conversation.messages.filter(role__in=("user", "assistant"))
        .values("id", "role", "content", "feedback", "created_at")
    )
    for item in messages:
        item["created_at"] = item["created_at"].isoformat()
    return JsonResponse({
        "conversation_id": conversation.external_id,
        "messages": messages,
        "is_archived": conversation.is_archived,
    })


@csrf_exempt
@require_POST
def chat(request):
    data, error_response = parse_json_body(request)
    if error_response:
        return error_response

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

    normalized_history = normalize_history(data.get("history"))
    if normalized_history is None:
        return JsonResponse(
            {"error": "invalid_history", "message": "History must be a JSON list."},
            status=400,
        )

    conversation = find_or_create_conversation(
        data.get("conversation_id"),
        request,
    )
    if not normalized_history:
        normalized_history = list(
            conversation.messages.order_by("-created_at")[:MAX_HISTORY_ITEMS]
            .values("role", "content")
        )[::-1]

    Message.objects.create(
        conversation=conversation,
        role="user",
        content=message,
    )
    record_event(
        "user_message",
        request,
        conversation=conversation,
        metadata={"message_length": len(message)},
    )

    started_at = perf_counter()
    try:
        answer = get_rag_service().ask(message, history=normalized_history)
    except Exception as exc:
        tb = traceback.format_exc()
        logger.exception("Exception while answering chat request: %s", exc)
        try:
            with ERROR_LOG.open("a", encoding="utf-8") as fh:
                fh.write("---\n")
                fh.write(tb)
                fh.write("\n")
        except OSError:
            pass
        record_event(
            "fallback_triggered",
            request,
            conversation=conversation,
            metadata={"error": str(exc)[:500]},
        )
        payload = {
            "error": "backend_error",
            "message": "The assistant is temporarily unavailable.",
        }
        if settings.DEBUG:
            payload["detail"] = str(exc)
        return JsonResponse(payload, status=500)

    answer = str(answer)
    latency_ms = round((perf_counter() - started_at) * 1000)
    assistant_message = Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=answer,
        latency_ms=latency_ms,
    )
    record_event(
        "assistant_answered",
        request,
        conversation=conversation,
        metadata={"latency_ms": latency_ms},
    )
    return JsonResponse({
        "answer": answer,
        "conversation_id": conversation.external_id,
        "message_id": assistant_message.id,
    })


@csrf_exempt
@require_POST
def events(request):
    data, error_response = parse_json_body(request)
    if error_response:
        return error_response
    event_type = data.get("event_type")
    if event_type not in EVENT_TYPES:
        return JsonResponse({"error": "invalid_event_type"}, status=400)
    conversation = find_or_create_conversation(data.get("conversation_id"), request)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    record_event(event_type, request, conversation, metadata)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def feedback(request):
    data, error_response = parse_json_body(request)
    if error_response:
        return error_response
    feedback_value = data.get("feedback")
    if feedback_value not in {"helpful", "not_helpful"}:
        return JsonResponse({"error": "invalid_feedback"}, status=400)
    conversation = Conversation.objects.filter(
        external_id=(data.get("conversation_id") or "").strip()[:100],
    ).first()
    if conversation is None:
        return JsonResponse({"error": "conversation_not_found"}, status=404)
    message = conversation.messages.filter(
        id=data.get("message_id"),
        role="assistant",
    ).first()
    if message is None:
        return JsonResponse({"error": "message_not_found"}, status=404)
    message.feedback = feedback_value
    message.save(update_fields=("feedback",))
    record_event(
        "answer_helpful" if feedback_value == "helpful" else "answer_not_helpful",
        request,
        conversation,
        {"message_id": message.id},
    )
    return JsonResponse({"ok": True})
