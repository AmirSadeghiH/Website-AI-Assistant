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


def _is_local_dev_origin(origin):
    """True for loopback origins that must stay usable in DEBUG.

    In local development the demo page (``/static/demo.html``) and the
    customizer preview iframe (``/panel/preview/``) both run on
    ``http://127.0.0.1:8000`` / ``http://localhost:8000``. Requiring the
    operator to add those origins to the allow-list or to paste an
    ``X-Widget-Key`` just to see the widget locally is hostile — and it is
    exactly what produced the wall of ``403 Widget access is not authorized``
    in the user's log. In ``DEBUG`` we therefore treat loopback as trusted
    and bypass the strict key/origin gate; production (``DEBUG=False``) is
    unchanged.
    """
    if not origin:
        return False
    try:
        from urllib.parse import urlparse
        parsed = urlparse(origin.strip())
        host = (parsed.hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or host.endswith(".localhost")
    except Exception:
        return False


def _host_is_loopback(host):
    h = (host or "").split(":")[0].strip().lower()
    return h in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or h.endswith(".localhost")


def _request_is_local(request):
    """True when the HTTP request itself is loopback / same-host local.

    ``_resolve_request_origin`` returns "" when the browser omits both
    ``Origin`` and ``Referer`` (common for same-origin ``fetch`` in some
    configurations) or when a non-browser client like the customizer's
    ``fetch`` omits them. In that case ``_is_local_dev_origin("")`` is
    False and the DEBUG bypass would never fire, even though
    ``REMOTE_ADDR`` is 127.0.0.1 and ``Host`` is ``127.0.0.1:8000``. We
    therefore also inspect ``Host`` and ``REMOTE_ADDR`` so the demo and
    the preview iframe stay usable in local development without a widget
    key.
    """
    origin = _resolve_request_origin(request)
    if _is_local_dev_origin(origin):
        return True
    try:
        host = request.get_host()
    except Exception:
        host = request.META.get("HTTP_HOST", "") or request.META.get("SERVER_NAME", "")
    if _host_is_loopback(host):
        return True
    remote = (request.META.get("REMOTE_ADDR") or "").strip()
    if remote in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        return True
    return False


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
        origin = _resolve_request_origin(request)

        # Local development exception: the demo page (``/static/demo.html``)
        # and the customizer preview iframe (``/panel/preview/``) run on
        # loopback. Requiring the operator to whitelist 127.0.0.1 or paste
        # the X-Widget-Key just to see the widget locally is hostile and is
        # exactly what produced the wall of 403s in the user's log.
        # In DEBUG we trust loopback unconditionally; production (DEBUG=False)
        # is unchanged and stays strict.
        if getattr(settings, "DEBUG", False) and _request_is_local(request):
            return True

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
        if origin and allowed_origins and not _origin_matches(origin, allowed_origins):
            return False

        return True
