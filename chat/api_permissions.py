import hashlib
import hmac
import json

from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import BasePermission

_INSTALL_CACHE_KEY = "ai-support:installation"
_INSTALL_CACHE_TTL = 10


def get_widget_access_config():
    """Resolve the widget public key and allowed origins.

    Admin-panel values (ProviderSettings) win over environment variables;
    blank panel values keep the environment fallback. The result is cached
    briefly so API requests do not hit the database, and changes made in the
    admin panel take effect within a few seconds. The cache key includes the
    environment values so ``override_settings`` in tests stays deterministic.
    """
    env_key = getattr(settings, "WIDGET_PUBLIC_KEY", "")
    env_origins = tuple(getattr(settings, "WIDGET_ALLOWED_ORIGINS", ()))
    fingerprint = hashlib.sha256(
        json.dumps(
            [env_key, env_origins],
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:24]
    cache_key = f"{_INSTALL_CACHE_KEY}:{fingerprint}"

    data = cache.get(cache_key)
    if data is None:
        widget_key = env_key
        origins = env_origins
        from .models import ProviderSettings

        provider = ProviderSettings.objects.first()
        if provider is not None:
            if provider.widget_public_key.strip():
                widget_key = provider.widget_public_key.strip()
            panel_origins = tuple(provider.allowed_origins_list)
            if panel_origins:
                origins = panel_origins
        data = (widget_key, origins)
        cache.set(cache_key, data, timeout=_INSTALL_CACHE_TTL)
    return data


class WidgetAccessPermission(BasePermission):
    """
    Public widget access is intentionally not tied to a Django login.
    Production deployments can require a per-installation public key and
    restrict browser origins. The key is not a secret; provider credentials
    must never be shipped to the browser. The key and origins are editable
    from the admin panel and fall back to environment variables.
    """

    message = "Widget access is not authorized."

    def has_permission(self, request, view):
        configured_key, allowed_origins = get_widget_access_config()
        supplied_key = request.headers.get("X-Widget-Key", "")
        if getattr(settings, "WIDGET_REQUIRE_KEY", False) and not configured_key:
            return False
        if configured_key and not hmac.compare_digest(
            str(supplied_key),
            str(configured_key),
        ):
            return False
        origin = request.headers.get("Origin", "").strip().rstrip("/")
        if origin and allowed_origins and origin not in allowed_origins:
            return False
        return True
