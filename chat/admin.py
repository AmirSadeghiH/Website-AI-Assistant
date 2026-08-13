from django.contrib import admin
from django.db.models import Count

from .models import AnalyticsEvent, Conversation, Message, Site, WidgetConfig


class WidgetConfigInline(admin.StackedInline):
    model = WidgetConfig
    extra = 0
    max_num = 1
    fieldsets = (
        ("Widget appearance", {
            "fields": (
                "title",
                "subtitle",
                "greeting",
                "primary_color",
                "secondary_color",
                "font_family",
                "position",
                "suggestions",
            ),
        }),
        ("Behavior and AI", {
            "fields": (
                "show_history",
                "allow_feedback",
                "show_powered_by",
                "temperature",
                "model_name",
                "system_prompt",
                "user_prompt",
            ),
        }),
    )


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "domain",
        "conversation_count",
        "message_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "domain", "public_key")
    readonly_fields = ("public_key", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (WidgetConfigInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _conversation_count=Count("conversations", distinct=True),
            _message_count=Count("conversations__messages", distinct=True),
        )

    @admin.display(description="Conversations", ordering="_conversation_count")
    def conversation_count(self, obj):
        return obj._conversation_count

    @admin.display(description="Messages", ordering="_message_count")
    def message_count(self, obj):
        return obj._message_count


@admin.register(WidgetConfig)
class WidgetConfigAdmin(admin.ModelAdmin):
    list_display = ("site", "title", "primary_color", "show_history", "updated_at")
    list_filter = ("show_history", "allow_feedback")
    search_fields = ("site__name", "site__slug", "title")
    readonly_fields = ("updated_at",)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    can_delete = False
    readonly_fields = ("role", "content", "feedback", "latency_ms", "created_at")
    fields = readonly_fields


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "site",
        "external_id",
        "message_count",
        "is_archived",
        "last_activity_at",
    )
    list_filter = ("site", "is_archived")
    search_fields = ("external_id", "site__name", "page_url")
    readonly_fields = ("started_at", "last_activity_at")
    inlines = (MessageInline,)

    @admin.display(description="Messages")
    def message_count(self, obj):
        return obj.messages.count()


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "feedback", "latency_ms", "created_at")
    list_filter = ("role", "feedback", "conversation__site")
    search_fields = ("content", "conversation__external_id")
    readonly_fields = ("created_at",)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("site", "event_type", "conversation", "created_at")
    list_filter = ("site", "event_type")
    search_fields = ("path", "conversation__external_id")
    readonly_fields = ("created_at",)
