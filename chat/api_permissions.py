from django.conf import settings
from rest_framework.permissions import BasePermission


class WidgetAccessPermission(BasePermission):
    """
    Public widget access is intentionally not tied to a Django login.
    Production deployments can require a per-installation public key and
    restrict browser origins. The key is not a secret; provider credentials
    must never be shipped to the browser.
    """

    message = "Widget access is not authorized."

    def has_permission(self, request, view):
        configured_key = getattr(settings, "WIDGET_PUBLIC_KEY", "")
        supplied_key = request.headers.get("X-Widget-Key", "")
        if getattr(settings, "WIDGET_REQUIRE_KEY", False) and not configured_key:
            return False
        if configured_key and supplied_key != configured_key:
            return False
        allowed_origins = set(getattr(settings, "WIDGET_ALLOWED_ORIGINS", ()))
        origin = request.headers.get("Origin", "").strip().rstrip("/")
        if origin and allowed_origins and origin not in allowed_origins:
            return False
        return True
