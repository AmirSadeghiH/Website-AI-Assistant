import fnmatch
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


def _origin_matches(origin, patterns):
    """Check if an origin matches any of the allowed patterns.

    Supports exact matches and wildcard patterns:
    - ``https://example.com`` — exact match
    - ``https://*.example.com`` — matches any subdomain
    - ``http://localhost:*`` — matches any port

    Always compares normalized (lower-cased, no trailing slash) values.
    """
    origin = origin.strip().rstrip("/").lower()
    if not origin:
        return False
    for pattern in patterns:
        pattern = pattern.strip().rstrip("/").lower()
        if not pattern:
            continue
        # Exact match (fast path)
        if origin == pattern:
            return True
        # Wildcard match via fnmatch
        if "*" in pattern:
            if fnmatch.fnmatch(origin, pattern):
                return True
    return False


def _resolve_request_origin(request):
    """Extract the request origin, falling back to Referer when Origin is absent.

    Browsers always send Origin on cross-origin requests, but some proxies
    strip it and non-browser HTTP clients (cURL, server-to-server) may send
    only Referer.  We use whichever is available, preferring Origin.
    """
    origin = request.headers.get("Origin", "").strip().rstrip("/")
    if origin:
        return origin
    referer = request.headers.get("Referer", "").strip().rstrip("/")
    if referer:
        # Extract origin from Referer URL (scheme + host + optional port)
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.scheme and parsed.hostname:
            origin = f"{parsed.scheme}://{parsed.hostname}"
            if parsed.port:
                origin += f":{parsed.port}"
            return origin
    return ""


class WidgetAccessPermission(BasePermission):
    """
    Public widget access is intentionally not tied to a Django login.
    Production deployments can require a per-installation public key and
    restrict browser origins. The key is not a secret; provider credentials
    must never be shipped to the browser. The key and origins are editable
    from the admin panel and fall back to environment variables.

    Security layers:
    1. Widget public key (X-Widget-Key header) — installation identifier.
    2. Origin validation with wildcard support — domain binding.
    3. Referer fallback for non-browser clients.
    """

    message = "Widget access is not authorized."

    def has_permission(self, request, view):
        configured_key, allowed_origins = get_widget_access_config()
        supplied_key = request.headers.get("X-Widget-Key", "")

        # Enforce key requirement in production
        if getattr(settings, "WIDGET_REQUIRE_KEY", False) and not configured_key:
            return False

        # Constant-time key comparison
        if configured_key and not hmac.compare_digest(
            str(supplied_key),
            str(configured_key),
        ):
            return False

        # Origin/Referer validation with wildcard matching
        origin = _resolve_request_origin(request)
        if origin and allowed_origins and not _origin_matches(origin, allowed_origins):
            return False

        return True
