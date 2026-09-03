from django.urls import path
from .views import (
    chat,
    chat_stream,
    events,
    feedback,
    handoff,
    health,
    history,
    leads,
    widget_config,
)

urlpatterns = [
    path("chat/", chat, name="chat"),
    path("chat/stream/", chat_stream, name="chat-stream"),
    path("health/", health, name="health"),
    path("widget-config/", widget_config, name="widget-config"),
    path("history/", history, name="history"),
    path("events/", events, name="events"),
    path("feedback/", feedback, name="feedback"),
    path("leads/", leads, name="leads"),
    path("handoff/", handoff, name="handoff"),
]
