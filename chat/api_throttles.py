from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class WidgetRateThrottle(SimpleRateThrottle):
    scope = "widget"

    def get_cache_key(self, request, view):
        ident = self._client_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }

    def _client_ident(self, request):
        # When the deployment sits behind a trusted reverse proxy, use the
        # left-most X-Forwarded-For address; otherwise every visitor shares
        # the proxy's REMOTE_ADDR and one bucket throttles the whole site.
        if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
            forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first:
                    return first
        return request.META.get("REMOTE_ADDR", "unknown")

    def get_rate(self):
        return getattr(settings, "WIDGET_RATE", "30/minute")


class WidgetEventsThrottle(WidgetRateThrottle):
    scope = "widget_events"

    def get_rate(self):
        return getattr(settings, "WIDGET_EVENTS_RATE", "120/minute")


class WidgetFeedbackThrottle(WidgetRateThrottle):
    scope = "widget_feedback"

    def get_rate(self):
        return getattr(settings, "WIDGET_FEEDBACK_RATE", "60/minute")
