from django.urls import path
from .views import (
    chat,
    events,
    feedback,
    health,
    widget_config,
)

urlpatterns = [
    path("chat/", chat, name="chat"),
    path("health/", health, name="health"),
    path("widget-config/", widget_config, name="widget-config"),
    path("events/", events, name="events"),
    path("feedback/", feedback, name="feedback"),
]
