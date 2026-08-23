import json
import logging
import threading
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response

from .api_permissions import WidgetAccessPermission, _resolve_request_origin
from .api_throttles import (
    WidgetEventsThrottle,
    WidgetFeedbackThrottle,
    WidgetKeyRateThrottle,
    WidgetRateThrottle,
)
from .models import AdminNotification, AnalyticsEvent, ProviderSettings, WidgetConfig
from .services import CorpusConfigError
from rag.retriever import EmbeddingDimensionMismatchError
from .serializers import ChatRequestSerializer, EventSerializer, FeedbackSerializer

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
        return None, Response(
            {"error": "invalid_payload", "message": "Invalid request payload."},
            status=400,
        )
    return serializer.validated_data, None


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
    # Resolve icon URL
    icon_url = ""
    if config.icon_type == "custom" and config.custom_icon_file:
        icon_url = config.custom_icon_file.url
    payload = {
        "business_name": config.business_name,
        "website_url": config.website_url,
        "title": config.title,
        "subtitle": config.subtitle,
        "greeting": config.greeting,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "accent_color": config.accent_color,
        "header_badge": config.header_badge,
        "bot_avatar_text": config.bot_avatar_text,
        "input_placeholder": config.input_placeholder,
        "theme_mode": config.theme_mode,
        "dark_mode": config.dark_mode,
        "bubble_style": config.bubble_style,
        "panel_width": config.panel_width,
        "panel_height": config.panel_height,
        "border_radius": config.border_radius,
        "mobile_fullscreen": config.mobile_fullscreen,
        "logo_url": config.logo_url,
        "font_family": config.font_family,
        "font_size": config.font_size,
        "position": config.position,
        "positionVerticalOffset": config.position_vertical_offset,
        "positionHorizontalOffset": config.position_horizontal_offset,
        "iconType": config.icon_type,
        "defaultIconChoice": config.default_icon_choice,
        "customIconUrl": icon_url,
        "showFeedback": config.show_feedback,
        "show_powered_by": config.show_powered_by,
        "show_timestamp": config.show_timestamp,
        "show_avatar": config.show_avatar,
        "enable_sounds": config.enable_sounds,
        "enable_animations": config.enable_animations,
        "suggestions": config.suggestions or [],
        "faq_url": config.faq_url,
        "privacy_url": config.privacy_url,
        "support_email": config.support_email,
    }
    return payload


CORPUS_ARTIFACTS = (
    Path(settings.BASE_DIR) / "Data" / "chunks.json",
    Path(settings.BASE_DIR) / "Data" / "metadata.json",
    Path(settings.BASE_DIR) / "Data" / "embeddings.npy",
)


def get_rag_service():
    global _rag_service, _rag_artifact_signature
    signature = tuple(
        (str(path), path.stat().st_mtime_ns if path.exists() else 0)
        for path in CORPUS_ARTIFACTS
    )
    with _rag_lock:
        config = get_widget_config()
        provider = _get_provider_row()
        signature += (
            config.updated_at.timestamp(),
            provider.updated_at.timestamp() if provider is not None else 0,
        )
        if _rag_service is None or signature != _rag_artifact_signature:
            from .document_pipeline import corpus_lock
            from .services import RAGService, get_provider_values

            try:
                with corpus_lock(timeout=10):
                    _rag_service = RAGService(
                        config=config,
                        provider=get_provider_values(),
                    )
            except RuntimeError as exc:
                raise CorpusConfigError(str(exc)) from exc
            _rag_artifact_signature = signature
        else:
            _rag_service.apply_config(config)
        return _rag_service


def _get_provider_row():
    return ProviderSettings.objects.first()


def _track_metrics(request, latency_ms=None, error=False):
    """Record metrics for admin dashboard."""
    event_type = "error_occurred" if error else "assistant_answered"
    metadata = {}
    if latency_ms is not None:
        metadata["latency_ms"] = latency_ms
    metadata["origin"] = _resolve_request_origin(request)[:200]
    try:
        AnalyticsEvent.objects.create(
            event_type=event_type,
            path=request.headers.get("Referer", "")[:1000],
            metadata=metadata,
        )
    except Exception:
        logger.warning("Failed to track analytics event", exc_info=True)


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

    existing = [path.exists() for path in CORPUS_ARTIFACTS]
    if all(existing):
        checks["corpus"] = "ok"
    elif not any(existing):
        checks["corpus"] = "ok"
    else:
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
@throttle_classes([WidgetRateThrottle, WidgetKeyRateThrottle])
def widget_config(request):
    response = Response(widget_config_payload(get_widget_config()))
    response["Cache-Control"] = "public, max-age=10, stale-while-revalidate=60"
    return response


@api_view(["POST"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetRateThrottle, WidgetKeyRateThrottle])
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

    started_at = perf_counter()
    try:
        answer = get_rag_service().ask(data["message"])
    except (CorpusConfigError, EmbeddingDimensionMismatchError) as exc:
        logger.error("Corpus/provider configuration error: %s", exc)
        _track_metrics(request, error=True)
        _notify_if_needed("corpus_config", str(exc))
        return Response(
            {
                "error": "corpus_config",
                "message": "The knowledge base needs attention. Please check the documents and provider settings.",
            },
            status=503,
        )
    except Exception as exc:
        logger.exception("Chat request failed: %s", type(exc).__name__)
        try:
            if settings.DEBUG:
                with ERROR_LOG.open("a", encoding="utf-8") as error_file:
                    error_file.write(f"---\n{type(exc).__name__}: {exc}\n")
        except OSError:
            pass
        _track_metrics(request, error=True)
        _notify_if_needed(type(exc).__name__, str(exc))
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
    if not answer:
        answer = "متأسفم، الان نمی‌توانم پاسخ بدهم. لطفاً کمی بعد دوباره تلاش کنید."
    latency_ms = round((perf_counter() - started_at) * 1000)
    _track_metrics(request, latency_ms=latency_ms)

    response = Response(
        {
            "answer": answer,
        }
    )
    response["Cache-Control"] = "no-store"
    return response


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
    try:
        AnalyticsEvent.objects.create(
            event_type=data["event_type"],
            path=request.headers.get("Referer", "")[:1000],
            metadata=data.get("metadata") or {},
        )
    except Exception:
        logger.warning("Failed to create analytics event", exc_info=True)
    return Response({"ok": True})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([WidgetAccessPermission])
@throttle_classes([WidgetFeedbackThrottle, WidgetKeyRateThrottle])
def feedback(request):
    """Accept user feedback (thumbs-up/down) with reliable persistence.

    Feedback is written synchronously to the database. If the write fails,
    the error is logged but the user still receives a success response to
    avoid a degraded experience (feedback is nice-to-have, not critical).
    """
    raw_data, parse_error = _parse_json(request)
    if parse_error:
        return parse_error
    data, validation_error = _validate(FeedbackSerializer(data=raw_data))
    if validation_error:
        return validation_error

    event_type = "answer_helpful" if data["helpful"] else "answer_not_helpful"
    metadata = {
        "question": data.get("question", "")[:500],
        "answer_preview": data.get("answer_preview", "")[:300],
        "session_id": data.get("session_id", "")[:100],
    }
    if data.get("comment"):
        metadata["comment"] = data["comment"][:500]

    try:
        AnalyticsEvent.objects.create(
            event_type=event_type,
            path=_resolve_request_origin(request)[:1000],
            metadata=metadata,
        )
    except Exception:
        # Log but don't fail the request — feedback is best-effort
        logger.warning(
            "Failed to persist feedback: %s=%s error=%s",
            event_type,
            metadata.get("question", "")[:50],
            exc_info=True,
        )

    return Response({"ok": True})


@api_view(["GET"])
@authentication_classes([])
def notifications(request):
    """Return unread admin notifications."""
    if not request.user or not request.user.is_staff:
        return Response({"detail": "Forbidden"}, status=403)
    unread = AdminNotification.objects.filter(is_read=False)[:20]
    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "severity": n.severity,
            "created_at": n.created_at.isoformat(),
        }
        for n in unread
    ]
    return Response({"notifications": data})


def _notify_if_needed(error_type, detail):
    """Create a notification for critical errors (rate-limited to once per 5 min)."""
    now = int(perf_counter())
    notify_key = f"monitor:notify:{error_type}:{now // 300}"
    if cache.get(notify_key):
        return
    cache.set(notify_key, True, timeout=300)
    severity = "critical" if error_type in ("corpus_config", "capacity_limited") else "warning"
    AdminNotification.objects.get_or_create(
        title=f"Chat error: {error_type}",
        severity=severity,
        defaults={"message": detail[:500]},
    )
