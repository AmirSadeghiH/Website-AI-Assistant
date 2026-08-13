import json
import logging
import traceback
import uuid
from time import perf_counter
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import AnalyticsEvent, Conversation, Message, Site, WidgetConfig

_rag_service = None
ERROR_LOG = Path(settings.BASE_DIR) / 'error_tracebacks.log'
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
MAX_HISTORY_ITEMS = 8
MAX_HISTORY_CONTENT_LENGTH = 2000
DEFAULT_SITE_SLUG = "demo"
EVENT_TYPES = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}


def get_rag_service():
    global _rag_service
    if _rag_service is None:
        from .services import RAGService
        _rag_service = RAGService()
    return _rag_service


def get_or_create_site(site_id=None):
    site_id = (site_id or DEFAULT_SITE_SLUG).strip()
    site = (
        Site.objects.filter(slug=site_id).first()
        or Site.objects.filter(public_key=site_id).first()
    )
    if site is None and settings.DEBUG and site_id == DEFAULT_SITE_SLUG:
        site = Site.objects.create(
            name="Demo site",
            slug=DEFAULT_SITE_SLUG,
            domain="localhost",
        )
        WidgetConfig.objects.create(site=site)
    if site is None or not site.is_active:
        return None
    return site


def site_config(site):
    config, _created = WidgetConfig.objects.get_or_create(site=site)
    return {
        "site_id": site.slug,
        "site_key": site.public_key,
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
    }


def find_or_create_conversation(site, external_id, request):
    external_id = (external_id or "").strip()[:100]
    if not external_id:
        external_id = f"server_{uuid.uuid4().hex}"
    conversation, created = Conversation.objects.get_or_create(
        site=site,
        external_id=external_id,
        defaults={
            "page_url": request.headers.get("Referer", "")[:1000],
            "referrer": request.headers.get("Origin", "")[:1000],
            "user_agent": request.headers.get("User-Agent", "")[:1000],
        },
    )
    if created:
        AnalyticsEvent.objects.create(
            site=site,
            conversation=conversation,
            event_type="conversation_started",
            path=request.headers.get("Referer", "")[:1000],
        )
    return conversation


def record_event(site, event_type, request, conversation=None, metadata=None):
    if event_type not in EVENT_TYPES:
        return
    AnalyticsEvent.objects.create(
        site=site,
        conversation=conversation,
        event_type=event_type,
        path=request.headers.get("Referer", "")[:1000],
        metadata=metadata or {},
    )


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "ai-support-platform"})


@require_GET
def widget_config(request):
    site = get_or_create_site(request.GET.get("site_id"))
    if site is None:
        return JsonResponse(
            {"error": "site_not_found", "message": "The requested site is not available."},
            status=404,
        )
    return JsonResponse(site_config(site))


@require_GET
def conversation_history(request):
    site = get_or_create_site(request.GET.get("site_id"))
    if site is None:
        return JsonResponse(
            {"error": "site_not_found", "message": "The requested site is not available."},
            status=404,
        )
    external_id = (request.GET.get("conversation_id") or "").strip()[:100]
    if not external_id:
        return JsonResponse({"messages": []})
    conversation = Conversation.objects.filter(
        site=site,
        external_id=external_id,
    ).first()
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

    site = get_or_create_site(data.get("site_id"))
    if site is None:
        return JsonResponse(
            {"error": "site_not_found", "message": "The requested site is not available."},
            status=404,
        )

    conversation = find_or_create_conversation(
        site,
        data.get("conversation_id"),
        request,
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

    if conversation is not None and not normalized_history:
        normalized_history = list(
            conversation.messages.order_by("-created_at")[:MAX_HISTORY_ITEMS]
            .values("role", "content")
        )[::-1]

    user_message = None
    if conversation is not None:
        user_message = Message.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )
        record_event(
            site,
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

    answer = str(answer)
    latency_ms = round((perf_counter() - started_at) * 1000)
    assistant_message = None
    if conversation is not None:
        assistant_message = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=answer,
            latency_ms=latency_ms,
        )
        record_event(
            site,
            "assistant_answered",
            request,
            conversation=conversation,
            metadata={"latency_ms": latency_ms},
        )

    return JsonResponse({
        "answer": answer,
        "conversation_id": conversation.external_id if conversation else None,
        "message_id": assistant_message.id if assistant_message else None,
    })


@csrf_exempt
@require_POST
def events(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "invalid_payload"}, status=400)

    site = get_or_create_site(data.get("site_id"))
    if site is None:
        return JsonResponse({"error": "site_not_found"}, status=404)
    conversation = find_or_create_conversation(site, data.get("conversation_id"), request)
    event_type = data.get("event_type")
    if event_type not in EVENT_TYPES:
        return JsonResponse({"error": "invalid_event_type"}, status=400)
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    record_event(site, event_type, request, conversation, metadata)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def feedback(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "invalid_payload"}, status=400)

    feedback_value = data.get("feedback")
    if feedback_value not in {"helpful", "not_helpful"}:
        return JsonResponse({"error": "invalid_feedback"}, status=400)
    site = get_or_create_site(data.get("site_id"))
    if site is None:
        return JsonResponse({"error": "site_not_found"}, status=404)
    conversation = find_or_create_conversation(site, data.get("conversation_id"), request)
    message_id = data.get("message_id")
    message = None
    if message_id and conversation is not None:
        message = conversation.messages.filter(
            id=message_id,
            role="assistant",
        ).first()
    if message is None:
        return JsonResponse({"error": "message_not_found"}, status=404)
    message.feedback = feedback_value
    message.save(update_fields=("feedback",))
    record_event(
        site,
        "answer_helpful" if feedback_value == "helpful" else "answer_not_helpful",
        request,
        conversation,
        {"message_id": message.id},
    )
    return JsonResponse({"ok": True})
