import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.cache import patch_vary_headers

from .api_permissions import get_widget_access_config


class PanelOriginCorsMiddleware:
    """Allow admin-panel-managed widget origins through CORS.

    django-cors-headers only reads the static settings list and does not
    accept callables, so origins added from the admin panel are handled
    here. This middleware must run BEFORE corsheaders: corsheaders
    short-circuits CORS preflights without calling get_response, so a
    post-processing middleware would never see them. Headers are only added
    when corsheaders did not already set them.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not request.path.startswith("/api/"):
            return response
        origin = request.headers.get("Origin", "").strip().rstrip("/")
        if not origin:
            return response
        allowed_origins = get_widget_access_config()[1]
        if (
            origin in allowed_origins
            and "Access-Control-Allow-Origin" not in response
        ):
            response["Access-Control-Allow-Origin"] = origin
            if request.method == "OPTIONS":
                response["Access-Control-Allow-Methods"] = ", ".join(
                    getattr(settings, "CORS_ALLOW_METHODS", ())
                ) or "GET, POST, OPTIONS"
                response["Access-Control-Allow-Headers"] = ", ".join(
                    getattr(settings, "CORS_ALLOW_HEADERS", ())
                )
            patch_vary_headers(response, ("Origin",))
        return response


class AdminLoginRateLimitMiddleware:
    """Brute-force protection on /admin/login/.

    Uses Django's cache backend (Redis in production, LocMem in dev).
    Default: 5 attempts per minute per IP. Blocked for 15 minutes.
    """

    MAX_ATTEMPTS = 5
    WINDOW = 60  # seconds
    BLOCK_DURATION = 15 * 60  # 15 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path == "/admin/login/"
            and request.method == "POST"
        ):
            ip = self._get_ip(request)
            block_key = f"admin:block:{ip}"
            if cache.get(block_key):
                return JsonResponse(
                    {
                        "error": "rate_limited",
                        "message": "Too many login attempts. Please try again later.",
                    },
                    status=429,
                )
            attempt_key = f"admin:attempts:{ip}"
            attempts = cache.get(attempt_key, 0)
            if attempts >= self.MAX_ATTEMPTS:
                cache.set(block_key, True, timeout=self.BLOCK_DURATION)
                cache.delete(attempt_key)
                return JsonResponse(
                    {
                        "error": "rate_limited",
                        "message": "Too many login attempts. Blocked for 15 minutes.",
                    },
                    status=429,
                )
        response = self.get_response(request)
        # After a failed login POST, increment the counter
        if (
            request.path == "/admin/login/"
            and request.method == "POST"
            and response.status_code == 200
            and hasattr(response, "content")
            and b"error" in response.content.lower()
        ):
            ip = self._get_ip(request)
            attempt_key = f"admin:attempts:{ip}"
            attempts = cache.get(attempt_key, 0)
            cache.set(attempt_key, attempts + 1, timeout=self.WINDOW)
        return response

    @staticmethod
    def _get_ip(request):
        if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
            forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first:
                    return first
        return request.META.get("REMOTE_ADDR", "unknown")


class SecurityHeadersMiddleware:
    """Add security headers to all responses.

    CSP is applied only to admin pages to avoid breaking the widget.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, "DEBUG", False):
            response.setdefault("X-Content-Type-Options", "nosniff")
            response.setdefault("X-Frame-Options", "SAMEORIGIN")
            response.setdefault("Referrer-Policy", "same-origin")
            response.setdefault(
                "Permissions-Policy",
                "camera=(), microphone=(), geolocation=()",
            )
        # CSP for admin only (widget is served via static files, no inline)
        if request.path.startswith("/admin/"):
            response.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'self';",
            )
        return response


class ApiRequestSizeLimitMiddleware:
    """Reject oversized or unbounded public API bodies before JSON parsing.

    Without a Content-Length header (e.g. Transfer-Encoding: chunked) the
    JSON parser would read the whole stream into memory with no bound, so
    body-carrying API requests must declare a Content-Length that is within
    the configured cap.
    """

    MAX_API_BODY_BYTES = 64 * 1024

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and request.method in (
            "POST", "PUT", "PATCH",
        ):
            content_length = request.META.get("CONTENT_LENGTH", "")
            transfer_encoding = (
                request.META.get("HTTP_TRANSFER_ENCODING", "").lower()
            )

            if transfer_encoding and "chunked" in transfer_encoding:
                return JsonResponse(
                    {
                        "error": "chunked_not_allowed",
                        "message": "Chunked request bodies are not supported.",
                    },
                    status=411,
                )
            if content_length == "":
                return JsonResponse(
                    {
                        "error": "content_length_required",
                        "message": "A Content-Length header is required.",
                    },
                    status=411,
                )
            try:
                size = int(content_length)
            except (TypeError, ValueError):
                return JsonResponse(
                    {"error": "invalid_content_length"}, status=400,
                )
            if size < 0 or size > self.MAX_API_BODY_BYTES:
                return JsonResponse(
                    {
                        "error": "payload_too_large",
                        "message": "Request payload is too large.",
                    },
                    status=413,
                )
        return self.get_response(request)


class MediaDocumentProtectionMiddleware:
    """Block direct HTTP access to uploaded source documents.

    In production, nginx handles this via location blocks. In development
    (DEBUG=True), Django serves media files, so this middleware provides
    the same protection for the ``media/documents/`` path.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith("/media/documents/")
            or request.path.startswith("/media/documents")
        ):
            from django.http import Http404
            raise Http404
        return self.get_response(request)


class RequestMonitoringMiddleware:
    """Track request latency and error rates; create admin notifications on pressure.

    Runs on every /api/ request. Tracks:
    - Total requests and errors in the last minute (sliding window).
    - Average latency in the last minute.
    - Creates AdminNotification when thresholds are exceeded.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        start = time.perf_counter()
        response = self.get_response(request)
        latency_ms = (time.perf_counter() - start) * 1000

        # Track metrics in cache (per-minute sliding window)
        minute_key = f"monitor:window:{int(time.time() // 60)}"
        window = cache.get(minute_key, {"count": 0, "errors": 0, "total_latency": 0})
        window["count"] += 1
        if response.status_code >= 500:
            window["errors"] += 1
        window["total_latency"] += latency_ms
        cache.set(minute_key, window, timeout=120)

        # Check thresholds
        self._check_thresholds(window, response.status_code)

        return response

    def _check_thresholds(self, window, status_code):
        from django.conf import settings as _settings

        error_threshold = getattr(_settings, "MONITORING_ERROR_THRESHOLD", 10)
        latency_threshold = getattr(_settings, "MONITORING_LATENCY_THRESHOLD_MS", 5000)

        # Rate limit notifications (once per 5 minutes per type)
        now = int(time.time())

        if window["errors"] >= error_threshold:
            notify_key = f"monitor:notified:errors:{now // 300}"
            if not cache.get(notify_key):
                self._notify(
                    title="Error rate spike detected",
                    message=f"{window['errors']} server errors in the last minute.",
                    severity="critical",
                )
                cache.set(notify_key, True, timeout=300)

        avg_latency = (
            window["total_latency"] / window["count"] if window["count"] else 0
        )
        if window["count"] >= 5 and avg_latency > latency_threshold:
            notify_key = f"monitor:notified:latency:{now // 300}"
            if not cache.get(notify_key):
                self._notify(
                    title="High latency detected",
                    message=f"Average response time: {avg_latency:.0f}ms over {window['count']} requests.",
                    severity="warning",
                )
                cache.set(notify_key, True, timeout=300)

    @staticmethod
    def _notify(title, message, severity="warning"):
        from .models import AdminNotification

        AdminNotification.objects.get_or_create(
            title=title,
            severity=severity,
            defaults={"message": message},
        )
