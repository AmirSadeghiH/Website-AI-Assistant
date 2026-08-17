from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models import Count, Q
from django import forms
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    AnalyticsEvent,
    Conversation,
    Document,
    Message,
    ProviderSettings,
    WidgetConfig,
)

_DASHBOARD_CACHE_KEY = "ai-support:dashboard-stats"


class SupportAdminSite(AdminSite):
    site_header = "AI Support Control Room"
    site_title = "AI Support Admin"
    index_title = "مرکز مدیریت و پایش دستیار هوشمند"
    index_template = "admin/chat_dashboard.html"

    def each_context(self, request):
        context = super().each_context(request)
        stats = cache.get(_DASHBOARD_CACHE_KEY)
        if stats is None:
            today = timezone.localdate()
            stats = {
                "conversations": Conversation.objects.count(),
                "messages": Message.objects.count(),
                "messages_today": Message.objects.filter(
                    created_at__date=today,
                ).count(),
                "helpful": Message.objects.filter(feedback="helpful").count(),
                "not_helpful": Message.objects.filter(
                    feedback="not_helpful"
                ).count(),
                "fallbacks": AnalyticsEvent.objects.filter(
                    event_type="fallback_triggered",
                ).count(),
            }
            cache.set(_DASHBOARD_CACHE_KEY, stats, timeout=30)
        context["dashboard_stats"] = stats
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
                    "header_badge",
                    "bot_avatar_text",
                    "input_placeholder",
                    "theme_mode",
                    "panel_width",
                    "panel_height",
                    "border_radius",
                    "mobile_fullscreen",
                    "logo_url",
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
                "description": (
                    "کلیدهای API، مدل embedding و ظرفیت در بخش جداگانه‌ی "
                    "«AI provider settings» تنظیم می‌شوند."
                ),
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
    from .document_pipeline import enqueue_documents

    count = enqueue_documents(queryset.values_list("pk", flat=True))
    modeladmin.message_user(
        request,
        f"{count} سند برای پردازش در پس‌زمینه صف شد.",
    )


class ProviderSettingsForm(forms.ModelForm):
    """Admin form that never round-trips stored API keys to the browser.

    Key fields render as password inputs; leaving them empty keeps the
    current stored value, so the secret is only written when a new value is
    typed.
    """

    llm_api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="کلید API مدل پاسخ‌دهنده. برای حفظ مقدار فعلی خالی بگذارید.",
    )
    embedding_api_key = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="کلید API سرویس embedding. برای حفظ مقدار فعلی خالی بگذارید.",
    )

    class Meta:
        model = ProviderSettings
        fields = (
            "llm_api_key",
            "llm_base_url",
            "llm_model",
            "llm_max_tokens",
            "llm_timeout_seconds",
            "llm_max_retries",
            "embedding_api_key",
            "embedding_base_url",
            "embedding_model",
            "embedding_timeout_seconds",
            "embedding_max_retries",
            "rag_max_concurrent",
            "response_cache_seconds",
            "widget_public_key",
            "widget_allowed_origins",
        )
        widgets = {
            "widget_allowed_origins": forms.Textarea(
                attrs={"rows": 5, "dir": "ltr"},
            ),
        }
        help_texts = {
            "widget_public_key": (
                "کلید عمومی نصب (در تگ ویجت مشتری قرار می‌گیرد). "
                "خالی = استفاده از متغیر محیطی WIDGET_PUBLIC_KEY. "
                "این مقدار secret نیست."
            ),
            "widget_allowed_origins": (
                "هر دامنه‌ی مجاز در یک خط؛ نمونه: https://example.com — "
                "این دامنه‌ها هم روی دسترسی API و هم روی CORS اعمال می‌شوند."
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        for field in ("llm_api_key", "embedding_api_key"):
            if not self.cleaned_data.get(field):
                current = (
                    getattr(self.instance, field)
                    if self.instance and self.instance.pk
                    else ""
                )
                setattr(instance, field, current)
        if commit:
            instance.save()
        return instance


class ProviderSettingsAdmin(admin.ModelAdmin):
    form = ProviderSettingsForm
    fieldsets = (
        (
            "مدل پاسخ‌دهنده (LLM)",
            {
                "fields": (
                    "llm_api_key",
                    "llm_base_url",
                    "llm_model",
                    "llm_max_tokens",
                    "llm_timeout_seconds",
                    "llm_max_retries",
                ),
                "description": (
                    "اگر خالی بگذارید، مقدار معادل از متغیر محیطی خوانده می‌شود. "
                    "کلیدها به‌صورت رمزنگاری‌شده در پایگاه داده ذخیره می‌شوند."
                ),
            },
        ),
        (
            "مدل Embedding",
            {
                "fields": (
                    "embedding_api_key",
                    "embedding_base_url",
                    "embedding_model",
                    "embedding_timeout_seconds",
                    "embedding_max_retries",
                ),
                "description": (
                    "هنگام تغییر مدل embedding، اسناد قبلی باید دوباره پردازش شوند "
                    "(دکمه ساخت embedding روی هر سند)."
                ),
            },
        ),
        (
            "ظرفیت و کش",
            {
                "fields": (
                    "rag_max_concurrent",
                    "response_cache_seconds",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "نصب ویجت و کنترل دسترسی",
            {
                "fields": (
                    "widget_public_key",
                    "widget_allowed_origins",
                ),
                "description": (
                    "برای افزودن مشتری جدید کافی است این‌جا کلید و دامنه‌ی سایتش "
                    "را وارد کنید؛ تا چند ثانیه بعد روی API و CORS اعمال می‌شود "
                    "و تگ ویجت آماده‌ی تحویل است."
                ),
            },
        ),
    )
    readonly_fields = ("updated_at",)
    list_display = (
        "llm_model_summary",
        "embedding_model_summary",
        "llm_key_set",
        "embedding_key_set",
        "widget_key_set",
        "updated_at",
    )

    @admin.display(description="مدل LLM")
    def llm_model_summary(self, obj):
        return obj.llm_model or "— (از محیط)"

    @admin.display(description="مدل Embedding")
    def embedding_model_summary(self, obj):
        return obj.embedding_model or "— (از محیط)"

    @admin.display(description="کلید LLM", boolean=True)
    def llm_key_set(self, obj):
        return bool(obj.llm_api_key)

    @admin.display(description="کلید Embedding", boolean=True)
    def embedding_key_set(self, obj):
        return bool(obj.embedding_api_key)

    @admin.display(description="کلید نصب ویجت", boolean=True)
    def widget_key_set(self, obj):
        return bool(obj.widget_public_key)

    def has_add_permission(self, request):
        return not ProviderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class DocumentAdminForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("title", "file")

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if not uploaded:
            return uploaded
        from .document_pipeline import MAX_DOCUMENT_BYTES, detect_file_type

        if not detect_file_type(uploaded.name):
            raise forms.ValidationError(
                "فرمت مجاز فقط PDF، TXT و DOCX است.",
            )
        if uploaded.size > MAX_DOCUMENT_BYTES:
            raise forms.ValidationError(
                "حجم فایل نباید بیشتر از ۲۵ مگابایت باشد.",
            )
        return uploaded


@admin.register(Document, site=admin_site)
class DocumentAdmin(admin.ModelAdmin):
    form = DocumentAdminForm
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
        from .document_pipeline import detect_file_type

        if obj.file and not obj.title:
            obj.title = obj.file.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        if obj.file:
            obj.file_type = detect_file_type(obj.file.name) or ""
        if change and "file" in form.changed_data:
            obj.status = "uploaded"
            obj.error_message = ""
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        from .document_pipeline import remove_document_embeddings

        remove_document_embeddings(obj.pk)
        file_field = obj.file
        super().delete_model(request, obj)
        if file_field:
            file_field.delete(save=False)

    def delete_queryset(self, request, queryset):
        for document in queryset:
            self.delete_model(request, document)

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        palette = {
            "ready": "success",
            "processing": "info",
            "queued": "warning",
            "failed": "danger",
        }
        color = palette.get(obj.status, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display(),
        )


class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "conversation", "path", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("path", "conversation__external_id")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


admin_site.register(WidgetConfig, WidgetConfigAdmin)
admin_site.register(ProviderSettings, ProviderSettingsAdmin)
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(AnalyticsEvent, AnalyticsEventAdmin)
admin_site.register(get_user_model(), UserAdmin)
admin_site.register(Group)
