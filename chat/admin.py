from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count, Q
from django.utils import timezone

from .document_pipeline import enqueue_document
from .models import AnalyticsEvent, Conversation, Document, Message, WidgetConfig


class SupportAdminSite(AdminSite):
    site_header = "AI Support Control Room"
    site_title = "AI Support Admin"
    index_title = "مرکز مدیریت و پایش دستیار هوشمند"
    index_template = "admin/index.html"

    def each_context(self, request):
        context = super().each_context(request)
        today = timezone.localdate()
        context["dashboard_stats"] = {
            "conversations": Conversation.objects.count(),
            "messages": Message.objects.count(),
            "messages_today": Message.objects.filter(
                created_at__date=today,
            ).count(),
            "helpful": Message.objects.filter(feedback="helpful").count(),
            "not_helpful": Message.objects.filter(feedback="not_helpful").count(),
            "fallbacks": AnalyticsEvent.objects.filter(
                event_type="fallback_triggered",
            ).count(),
        }
        context["dashboard_recent"] = Conversation.objects.prefetch_related(
            "messages",
        )[:6]
        return context


admin_site = SupportAdminSite(name="admin")


class WidgetConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "پروفایل کسب‌وکار",
            {
                "fields": (
                    "business_name",
                    "website_url",
                    "faq_url",
                    "privacy_url",
                    "support_email",
                ),
            },
        ),
        (
            "ظاهر ویجت",
            {
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
            },
        ),
        (
            "رفتار و تجربه کاربر",
            {
                "fields": (
                    "show_history",
                    "allow_feedback",
                    "show_powered_by",
                ),
            },
        ),
        (
            "تنظیمات هوش مصنوعی",
            {
                "fields": (
                    "temperature",
                    "model_name",
                    "system_prompt",
                    "user_prompt",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    list_display = (
        "business_name",
        "title",
        "primary_color",
        "temperature",
        "updated_at",
    )
    search_fields = ("business_name", "title", "website_url")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not WidgetConfig.objects.exists()


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    can_delete = False
    readonly_fields = ("role", "content", "feedback", "latency_ms", "created_at")
    fields = readonly_fields


class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "external_id",
        "message_count",
        "feedback_count",
        "is_archived",
        "last_activity_at",
    )
    list_filter = ("is_archived", "started_at")
    search_fields = ("external_id", "page_url", "referrer")
    readonly_fields = ("started_at", "last_activity_at", "user_agent")
    inlines = (MessageInline,)
    date_hierarchy = "started_at"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _message_count=Count("messages", distinct=True),
            _feedback_count=Count(
                "messages",
                filter=~Q(messages__feedback=""),
                distinct=True,
            ),
        )

    @admin.display(description="پیام‌ها", ordering="_message_count")
    def message_count(self, obj):
        return obj._message_count

    @admin.display(description="بازخورد", ordering="_feedback_count")
    def feedback_count(self, obj):
        return obj._feedback_count


class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "conversation",
        "role",
        "feedback",
        "latency_ms",
        "created_at",
    )
    list_filter = ("role", "feedback", "created_at")
    search_fields = ("content", "conversation__external_id")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.action(description="شروع پردازش و ساخت embedding برای اسناد انتخاب‌شده")
def process_documents(modeladmin, request, queryset):
    count = 0
    for document in queryset.exclude(status__in=("queued", "processing")):
        enqueue_document(document.pk)
        count += 1
    modeladmin.message_user(
        request,
        f"{count} سند برای پردازش در پس‌زمینه صف شد.",
    )


@admin.register(Document, site=admin_site)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "file_type",
        "status_badge",
        "chunk_count",
        "embedding_count",
        "processed_at",
        "updated_at",
    )
    list_filter = ("status", "file_type", "created_at")
    search_fields = ("title", "file", "error_message")
    readonly_fields = (
        "file_type",
        "status",
        "error_message",
        "content_hash",
        "chunk_count",
        "embedding_count",
        "processed_at",
        "created_at",
        "updated_at",
    )
    actions = (process_documents,)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "سند دانش",
            {
                "fields": ("title", "file"),
                "description": "فرمت‌های مجاز: PDF، TXT و DOCX — حداکثر ۲۵ مگابایت.",
            },
        ),
        (
            "وضعیت پردازش",
            {
                "fields": (
                    "file_type",
                    "status",
                    "chunk_count",
                    "embedding_count",
                    "processed_at",
                    "content_hash",
                    "error_message",
                ),
            },
        ),
        (
            "اطلاعات ثبت",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if obj.file and not obj.title:
            obj.title = obj.file.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        super().save_model(request, obj, form, change)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        return obj.get_status_display()


class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "conversation", "path", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("path", "conversation__external_id")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


admin_site.register(WidgetConfig, WidgetConfigAdmin)
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(AnalyticsEvent, AnalyticsEventAdmin)
