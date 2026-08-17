from django.conf import settings
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
            "POST",
            "PUT",
            "PATCH",
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
                    {"error": "invalid_content_length"},
                    status=400,
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
