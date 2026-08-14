from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class WidgetRateThrottle(SimpleRateThrottle):
    scope = "widget"

    def get_cache_key(self, request, view):
        # REMOTE_ADDR is preferred; only trust forwarded headers after the
        # reverse proxy is configured to overwrite them.
        ident = request.META.get("REMOTE_ADDR", "unknown")
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }

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
