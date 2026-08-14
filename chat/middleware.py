from django.http import JsonResponse


class ApiRequestSizeLimitMiddleware:
    """Reject oversized public API bodies before JSON parsing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            content_length = request.META.get("CONTENT_LENGTH")
            try:
                if content_length and int(content_length) > 64 * 1024:
                    return JsonResponse(
                        {
                            "error": "payload_too_large",
                            "message": "Request payload is too large.",
                        },
                        status=413,
                    )
            except (TypeError, ValueError):
                return JsonResponse(
                    {"error": "invalid_content_length"},
                    status=400,
                )
        return self.get_response(request)
