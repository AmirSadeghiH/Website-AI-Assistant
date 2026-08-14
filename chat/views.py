import hashlib
import hmac
import json
import logging
import threading
import uuid
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response

from .api_permissions import WidgetAccessPermission
from .api_throttles import (
    WidgetEventsThrottle,
    WidgetFeedbackThrottle,
    WidgetRateThrottle,
)
from .models import AnalyticsEvent, Conversation, Message, WidgetConfig
from .serializers import (
    ChatRequestSerializer,
    EventSerializer,
    FeedbackSerializer,
    HistoryQuerySerializer,
)

logger = logging.getLogger(__name__)
_rag_service = None
_rag_artifact_signature = None
_rag_lock = threading.RLock()
_config_cache_key = "ai-support:widget-config"
ERROR_LOG = Path(settings.BASE_DIR) / "error_tracebacks.log"
EVENT_TYPES = {choice[0] for choice in AnalyticsEvent.EVENT_CHOICES}
CLIENT_EVENT_TYPES = {"widget_loaded", "fallback_triggered"}


def _parse_json(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, Response(
            {"error": "invalid_json", "message": "Request body must be valid JSON."},
            status=400,
        )
    if not isinstance(data, dict):
        return None, Response(
            {
                "error": "invalid_payload",
                "message": "Request body must be a JSON object.",
            },
            status=400,
        )
    return data, None


def _validate(serializer):
    try:
        serializer.is_valid(raise_exception=True)
    except ParseError:
        return None, Response(
            {"error": "invalid_json", "message": "Request body must be valid JSON."},
            status=400,
        )
    except ValidationError as exc:
        detail = exc.detail
        if isinstance(detail, dict) and "message" in detail:
            errors = detail["message"]
            first = errors[0] if isinstance(errors, list) else errors
            code = getattr(first, "code", "")
            if code == "max_length":
                return None, Response(
                    {
                        "error": "message_too_long",
                        "message": "The message is too long.",
                    },
                    status=413,
                )
            if code in {"blank", "required"}:
                return None, Response(
                    {"error": "message_required", "message": "The message is required."},
                    status=400,
                )
            return None, Response(
                {"error": "invalid_message", "message": "The message is invalid."},
                status=400,
            )
        if isinstance(detail, dict) and "history" in detail:
            return None, Response(
                {"error": "invalid_history", "message": "History must be a JSON list."},
                status=400,
            )
        return None, Response(
            {"error": "invalid_payload", "message": "Invalid request payload."},
            status=400,
        )
    return serializer.validated_data, None


def _conversation_token(external_id):
    return hmac.new(
        str(settings.SECRET_KEY).encode("utf-8"),
        external_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _valid_conversation_token(external_id, token):
    return bool(token) and hmac.compare_digest(
        _conversation_token(external_id),
        str(token),
    )


def get_widget_config():
    config = cache.get(_config_cache_key)
    if config is None:
        config = WidgetConfig.objects.first()
        if config is None:
            try:
                config = WidgetConfig.objects.create()
            except IntegrityError:
                config = WidgetConfig.objects.first()
        cache.set(_config_cache_key, config, timeout=10)
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
        "header_badge": config.header_badge,
        "bot_avatar_text": config.bot_avatar_text,
        "input_placeholder": config.input_placeholder,
        "theme_mode": config.theme_mode,
        "panel_width": config.panel_width,
        "panel_height": config.panel_height,
        "border_radius": config.border_radius,
        "mobile_fullscreen": config.mobile_fullscreen,
        "logo_url": config.logo_url,
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


def get_rag_service():
    global _rag_service, _rag_artifact_signature
    artifact_paths = (
        Path(settings.BASE_DIR) / "Data" / "chunks.json",
        Path(settings.BASE_DIR) / "Data" / "metadata.json",
        Path(settings.BASE_DIR) / "Data" / "embeddings.npy",
    )
    signature = tuple(
        (str(path), path.stat().st_mtime_ns if path.exists() else 0)
        for path in artifact_paths
    )
    with _rag_lock:
        config = get_widget_config()
        if _rag_service is None or signature != _rag_artifact_signature:
            from .services import RAGService
            from .document_pipeline import corpus_lock

            with corpus_lock(timeout=10):
                _rag_service = RAGService(config=config)
            _rag_artifact_signature = signature
        else:
            _rag_service.apply_config(config)
        return _rag_service


def find_or_create_conversation(external_id, request, conversation_token=""):
    external_id = (external_id or "").strip()[:100]
    if not external_id:
        external_id = f"conversation_{uuid.uuid4().hex}"
    conversation = Conversation.objects.filter(external_id=external_id).first()
    if conversation is not None:
        if getattr(settings, "WIDGET_PUBLIC_KEY", "") and not _valid_conversation_token(
            external_id,
            conversation_token,
        ):
            return None, False
        return conversation, False

    try:
        conversation = Conversation.objects.create(
            external_id=external_id,
            page_url=request.headers.get("Referer", "")[:1000],
            referrer=request.headers.get("Origin", "")[:1000],
            user_agent=request.headers.get("User-Agent", "")[:1000],
        )
    except IntegrityError:
        conversation = Conversation.objects.filter(external_id=external_id).first()
        if conversation is None:
            raise
        if getattr(settings, "WIDGET_PUBLIC_KEY", "") and not _valid_conversation_token(
            external_id,
            conversation_token,
        ):
            return None, False
        return conversation, False
    AnalyticsEvent.objects.create(
        conversation=conversation,
        event_type="conversation_started",
        path=request.headers.get("Referer", "")[:1000],
    )
    return conversation, True


def record_event(event_type, request, conversation=None, metadata=None):
    if event_type not in EVENT_TYPES:
        return
    AnalyticsEvent.objects.create(
        conversation=conversation,
        event_type=event_type,
        path=request.headers.get("Referer", "")[:1000],
        metadata=metadata or {},
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetRateThrottle])
def health(request):
    from django.db import connection

    checks = {"database": "ok", "corpus": "ok"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        checks["database"] = "error"

    artifact_paths = (
        Path(settings.BASE_DIR) / "Data" / "chunks.json",
        Path(settings.BASE_DIR) / "Data" / "metadata.json",
        Path(settings.BASE_DIR) / "Data" / "embeddings.npy",
    )
    if not all(path.exists() for path in artifact_paths):
        checks["corpus"] = "error"
    healthy = all(value == "ok" for value in checks.values())
    return Response(
        {
            "status": "ok" if healthy else "degraded",
            "service": "ai-support-platform",
            "version": settings.APP_VERSION,
            "mode": "single-site",
            "checks": checks,
        },
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetRateThrottle])
def widget_config(request):
    response = Response(widget_config_payload(get_widget_config()))
    response["Cache-Control"] = "public, max-age=10, stale-while-revalidate=60"
    return response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetRateThrottle])
def conversation_history(request):
    serializer = HistoryQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    external_id = serializer.validated_data["conversation_id"]
    if not external_id:
        return Response({"messages": []})
    conversation = Conversation.objects.filter(external_id=external_id).first()
    if conversation is None:
        return Response({"messages": []})
    if getattr(settings, "WIDGET_PUBLIC_KEY", "") and not _valid_conversation_token(
        external_id,
        request.headers.get("X-Conversation-Token", ""),
    ):
        return Response({"detail": "Conversation access denied."}, status=403)
    messages = list(
        conversation.messages.filter(role__in=("user", "assistant"))
        .values("id", "role", "content", "feedback", "created_at")
    )
    for item in messages:
        item["created_at"] = item["created_at"].isoformat()
    return Response(
        {
            "conversation_id": conversation.external_id,
            "messages": messages,
            "is_archived": conversation.is_archived,
        }
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetRateThrottle])
def chat(request):
    raw_data, parse_error = _parse_json(request)
    if parse_error:
        return parse_error
    if "message" in raw_data and not isinstance(raw_data["message"], str):
        return Response(
            {"error": "invalid_message", "message": "The message must be a string."},
            status=400,
        )
    data, validation_error = _validate(ChatRequestSerializer(data=raw_data))
    if validation_error:
        return validation_error
    conversation_token = request.headers.get("X-Conversation-Token", "")
    conversation, _created = find_or_create_conversation(
        data.get("conversation_id"),
        request,
        conversation_token,
    )
    if conversation is None:
        return Response({"detail": "Conversation access denied."}, status=403)

    history = data.get("history") or list(
        conversation.messages.order_by("-created_at")[:8].values("role", "content")
    )[::-1]
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=data["message"],
    )
    record_event(
        "user_message",
        request,
        conversation=conversation,
        metadata={"message_length": len(data["message"])},
    )

    started_at = perf_counter()
    try:
        answer = get_rag_service().ask(data["message"], history=history)
    except Exception as exc:
        logger.exception("Chat request failed: %s", type(exc).__name__)
        try:
            if settings.DEBUG:
                with ERROR_LOG.open("a", encoding="utf-8") as error_file:
                    error_file.write(f"---\n{type(exc).__name__}: {exc}\n")
        except OSError:
            pass
        record_event(
            "fallback_triggered",
            request,
            conversation=conversation,
            metadata={"error_type": type(exc).__name__},
        )
        if getattr(exc, "retry_after", None):
            return Response(
                {
                    "error": "capacity_limited",
                    "message": "The assistant is busy. Please try again shortly.",
                },
                status=429,
                headers={"Retry-After": str(exc.retry_after)},
            )
        return Response(
            {
                "error": "backend_error",
                "message": "The assistant is temporarily unavailable.",
            },
            status=503,
        )

    answer = str(answer).strip()
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
    return Response(
        {
            "answer": answer,
            "conversation_id": conversation.external_id,
            "conversation_token": _conversation_token(conversation.external_id),
            "message_id": assistant_message.id,
        }
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetEventsThrottle])
def events(request):
    raw_data, parse_error = _parse_json(request)
    if parse_error:
        return parse_error
    data, validation_error = _validate(EventSerializer(data=raw_data))
    if validation_error:
        return validation_error
    if data["event_type"] not in CLIENT_EVENT_TYPES:
        return Response({"error": "event_not_client_writable"}, status=403)
    conversation, _created = find_or_create_conversation(
        data.get("conversation_id"),
        request,
        request.headers.get("X-Conversation-Token", ""),
    )
    if conversation is None:
        return Response({"detail": "Conversation access denied."}, status=403)
    record_event(
        data["event_type"],
        request,
        conversation,
        data.get("metadata") or {},
    )
    return Response(
        {
            "ok": True,
            "conversation_id": conversation.external_id,
            "conversation_token": _conversation_token(conversation.external_id),
        }
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetFeedbackThrottle])
def feedback(request):
    raw_data, parse_error = _parse_json(request)
    if parse_error:
        return parse_error
    data, validation_error = _validate(FeedbackSerializer(data=raw_data))
    if validation_error:
        return validation_error
    conversation = Conversation.objects.filter(
        external_id=data["conversation_id"],
    ).first()
    if conversation is None:
        return Response({"error": "conversation_not_found"}, status=404)
    if getattr(settings, "WIDGET_PUBLIC_KEY", "") and not _valid_conversation_token(
        data["conversation_id"],
        request.headers.get("X-Conversation-Token", ""),
    ):
        return Response({"detail": "Conversation access denied."}, status=403)
    message = conversation.messages.filter(
        id=data["message_id"],
        role="assistant",
    ).first()
    if message is None:
        return Response({"error": "message_not_found"}, status=404)
    message.feedback = data["feedback"]
    message.save(update_fields=("feedback",))
    record_event(
        "answer_helpful"
        if data["feedback"] == "helpful"
        else "answer_not_helpful",
        request,
        conversation,
        {"message_id": message.id},
    )
    return Response({"ok": True})
