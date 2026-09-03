"""Custom admin panel URLconf — mounted at /panel/ from config/urls.py."""

from django.urls import path

from . import panel

app_name = "panel"

urlpatterns = [
    path("", panel.dashboard, name="dashboard"),
    path("conversations/", panel.conversations, name="conversations"),
    path("conversations/<int:pk>/", panel.conversation_detail, name="conversation-detail"),
    path("unanswered/", panel.unanswered, name="unanswered"),
    path("unanswered/<int:pk>/toggle/", panel.unanswered_toggle, name="unanswered-toggle"),
    path("leads/", panel.leads, name="leads"),
    path("leads/<int:pk>/action/", panel.leads_update, name="leads-update"),
    path("handoff/", panel.handoff_requests, name="handoff"),
    path("handoff/<int:pk>/action/", panel.handoff_update, name="handoff-update"),
    path("knowledge/", panel.knowledge, name="knowledge"),
    path("knowledge/<int:pk>/delete/", panel.knowledge_delete, name="knowledge-delete"),
    path("customizer/", panel.customizer, name="customizer"),
    path("preview/", panel.preview, name="preview"),
    path("installation/", panel.installation, name="installation"),
    path("installation/rotate-key/", panel.installation_key, name="installation-rotate-key"),
    path("wizard/", panel.wizard, name="wizard"),
    path("ai-settings/", panel.ai_settings, name="ai-settings"),
    path("business-rules/", panel.business_rules, name="business-rules"),
    path("health-summary/", panel.health_summary, name="health-summary"),
]
