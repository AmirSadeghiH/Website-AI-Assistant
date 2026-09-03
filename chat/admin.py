from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django import forms
from django.urls import path
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.http import JsonResponse

from .models import (
    AdminNotification,
    AnalyticsEvent,
    BusinessRule,
    Conversation,
    CrawlJob,
    Document,
    Feedback,
    HandoffRequest,
    Lead,
    Message,
    ProviderSettings,
    UnansweredQuestion,
    WidgetConfig,
)

_DASHBOARD_CACHE_KEY = "ai-support:dashboard-stats"


class SupportAdminSite(AdminSite):
    site_header = "AI Support Control Room"
    site_title = "AI Support Admin"
    index_title = "مرکز مدیریت و پایش دستیار هوشمند"
    index_template = "admin/chat_dashboard.html"

    def get_urls(self):
        custom_urls = [
            path(
                "notifications-mark-read/",
                self.admin_view(self._mark_notifications_read),
                name="notifications-read",
            ),
            path(
                "analytics-data/",
                self.admin_view(self._analytics_data_api),
                name="analytics-data",
            ),
            path(
                "faq-leaderboard/",
                self.admin_view(self._faq_leaderboard_api),
                name="faq-leaderboard",
            ),
        ]
        return custom_urls + super().get_urls()

    def _mark_notifications_read(self, request):
        AdminNotification.objects.filter(is_read=False).update(is_read=True)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/admin/"))

    def _analytics_data_api(self, request):
        """Return usage analytics aggregated by day/week/month for Chart.js."""
        if not request.user or not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)

        period = request.GET.get("period", "day")
        days = int(request.GET.get("days", "30"))
        cutoff = timezone.now() - timezone.timedelta(days=days)

        cache_key = f"analytics:{period}:{days}"
        data = cache.get(cache_key)
        if data is None:
            qs = AnalyticsEvent.objects.filter(created_at__gte=cutoff)

            if period == "month":
                trunc = TruncMonth("created_at")
            elif period == "week":
                trunc = TruncWeek("created_at")
            else:
                trunc = TruncDate("created_at")

            # Messages per period
            messages = (
                qs.filter(event_type="assistant_answered")
                .annotate(date=trunc)
                .values("date")
                .annotate(count=Count("id"))
                .order_by("date")
            )

            # Errors per period
            errors = (
                qs.filter(event_type="error_occurred")
                .annotate(date=trunc)
                .values("date")
                .annotate(count=Count("id"))
                .order_by("date")
            )

            # Widget loads per period
            loads = (
                qs.filter(event_type="widget_loaded")
                .annotate(date=trunc)
                .values("date")
                .annotate(count=Count("id"))
                .order_by("date")
            )

            # Helpful / not helpful
            helpful = qs.filter(event_type="answer_helpful").count()
            not_helpful = qs.filter(event_type="answer_not_helpful").count()

            # Average latency — compute in Python to avoid SQLite JSON field issues
            latency_values = (
                qs.filter(event_type="assistant_answered")
                .exclude(metadata__latency_ms=None)
                .values_list("metadata", flat=True)[:500]
            )
            latencies = [
                m.get("latency_ms", 0)
                for m in latency_values
                if isinstance(m, dict) and m.get("latency_ms")
            ]
            avg_latency = round(sum(latencies) / len(latencies)) if latencies else 0

            data = {
                "messages": [{"date": r["date"].isoformat(), "count": r["count"]} for r in messages],
                "errors": [{"date": r["date"].isoformat(), "count": r["count"]} for r in errors],
                "loads": [{"date": r["date"].isoformat(), "count": r["count"]} for r in loads],
                "helpful": helpful,
                "not_helpful": not_helpful,
                "avg_latency_ms": avg_latency,
                "total_messages": qs.filter(event_type="assistant_answered").count(),
                "total_errors": qs.filter(event_type="error_occurred").count(),
            }
            cache.set(cache_key, data, timeout=60)

        return JsonResponse(data)

    def _faq_leaderboard_api(self, request):
        """Return the most frequently asked questions."""
        if not request.user or not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)

        days = int(request.GET.get("days", "30"))
        limit = int(request.GET.get("limit", "15"))
        cutoff = timezone.now() - timezone.timedelta(days=days)

        cache_key = f"faq-leaderboard:{days}:{limit}"
        data = cache.get(cache_key)
        if data is None:
            # Extract questions from user_message events and answer_helpful metadata
            questions = []

            # From answer_helpful/answer_not_helpful events (has question in metadata)
            feedback_events = (
                AnalyticsEvent.objects.filter(
                    event_type__in=("answer_helpful", "answer_not_helpful"),
                    created_at__gte=cutoff,
                )
                .exclude(metadata__question="")
                .values_list("metadata", flat=True)
            )
            question_counts = {}
            for meta in feedback_events:
                q = (meta.get("question", "") or "").strip()[:200]
                if q:
                    question_counts[q] = question_counts.get(q, 0) + 1

            # Sort by frequency
            sorted_questions = sorted(
                question_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]

            data = [
                {"question": q, "count": c}
                for q, c in sorted_questions
            ]
            cache.set(cache_key, data, timeout=120)

        return JsonResponse({"questions": data})

    def each_context(self, request):
        context = super().each_context(request)
        stats = cache.get(_DASHBOARD_CACHE_KEY)
        if stats is None:
            today = timezone.localdate()
            one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
            error_count = AnalyticsEvent.objects.filter(
                event_type="error_occurred",
                created_at__gte=one_minute_ago,
            ).count()
            message_count = AnalyticsEvent.objects.filter(
                event_type="assistant_answered",
                created_at__gte=one_minute_ago,
            ).count()
            stats = {
                "documents": Document.objects.count(),
                "documents_ready": Document.objects.filter(status="ready").count(),
                "events_today": AnalyticsEvent.objects.filter(
                    created_at__date=today,
                ).count(),
                "errors_this_minute": error_count,
                "messages_this_minute": message_count,
                "unread_notifications": AdminNotification.objects.filter(
                    is_read=False,
                ).count(),
            }
            cache.set(_DASHBOARD_CACHE_KEY, stats, timeout=15)
        context["dashboard_stats"] = stats
        context["dashboard_notifications"] = AdminNotification.objects.filter(
            is_read=False,
        )[:10]
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
                    "accent_color",
                    "header_badge",
                    "bot_avatar_text",
                    "input_placeholder",
                    "theme_mode",
                    "dark_mode",
                    "bubble_style",
                    "panel_width",
                    "panel_height",
                    "border_radius",
                    "mobile_fullscreen",
                    "logo_url",
                    "font_family",
                    "font_size",
                    "suggestions",
                ),
            },
        ),
        (
            "موقعیت ویجت",
            {
                "fields": (
                    "position",
                    "position_vertical_offset",
                    "position_horizontal_offset",
                ),
                "description": (
                    "موقعیت ویجت روی صفحه. فاصله‌ها بر حسب پیکسل از لبه صفحه."
                ),
            },
        ),
        (
            "آیکون ویجت",
            {
                "fields": (
                    "icon_type",
                    "default_icon_choice",
                    "custom_icon_file",
                ),
                "description": (
                    "آیکون دکمه شناور (FAB). «پیش‌فرض» شامل ۶ آیکون آماده است. "
                    "«سفارشی» امکان آپلود فایل PNG/SVG را فراهم می‌کند."
                ),
            },
        ),
        (
            "رفتار و تجربه کاربر",
            {
                "fields": (
                    "show_feedback",
                    "show_powered_by",
                    "show_timestamp",
                    "show_avatar",
                    "enable_sounds",
                    "enable_animations",
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


class ProviderSettingsForm(forms.ModelForm):
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
                "خالی = استفاده از متغیر محیطی WIDGET_PUBLIC_KEY."
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
                    "هنگام تغییر مدل embedding، اسناد قبلی باید دوباره پردازش شوند."
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
                    "را وارد کنید؛ تا چند ثانیه بعد روی API و CORS اعمال می‌شود."
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
    actions = ("process_documents_action",)
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

    @admin.action(description="شروع پردازش و ساخت embedding برای اسناد انتخاب‌شده")
    def process_documents_action(self, request, queryset):
        from .document_pipeline import enqueue_documents

        count = enqueue_documents(queryset.values_list("pk", flat=True))
        self.message_user(
            request,
            f"{count} سند برای پردازش در پس‌زمینه صف شد.",
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


class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "is_read", "created_at")
    list_filter = ("severity", "is_read", "created_at")
    readonly_fields = ("title", "message", "severity", "created_at")
    actions = ("mark_read",)

    @admin.action(description="علامت‌گذاری به‌عنوان خوانده‌شده")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    def has_add_permission(self, request):
        return False


class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "path", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("path",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


class ConversationAdmin(admin.ModelAdmin):
    list_display = ("conversation_id", "status", "first_intent", "last_intent",
                    "message_count", "origin", "created_at", "updated_at")
    list_filter = ("status", "origin", "first_intent", "created_at")
    search_fields = ("conversation_id", "messages__content")
    readonly_fields = ("conversation_id", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = ()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("messages")


class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "intent", "used_fallback",
                    "is_streamed", "latency_ms", "created_at")
    list_filter = ("role", "intent", "used_fallback", "is_streamed")
    search_fields = ("content",)
    raw_id_fields = ("conversation",)
    readonly_fields = ("created_at",)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("message", "helpful", "has_comment", "created_at")
    list_filter = ("helpful", "created_at")
    raw_id_fields = ("message",)

    @admin.display(boolean=True, description="نظر دارد")
    def has_comment(self, obj):
        return bool(obj.comment)


class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "source", "conversation",
                    "notified", "created_at")
    list_filter = ("source", "notified", "created_at")
    search_fields = ("name", "email", "phone", "note")
    raw_id_fields = ("conversation",)


class HandoffRequestAdmin(admin.ModelAdmin):
    list_display = ("channel", "status", "question", "conversation",
                    "notified", "created_at")
    list_filter = ("channel", "status", "created_at")
    search_fields = ("question",)
    raw_id_fields = ("conversation",)


class UnansweredQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "count", "reason", "last_intent",
                    "is_resolved", "updated_at")
    list_filter = ("reason", "is_resolved", "last_intent")
    search_fields = ("question",)

    @admin.action(description="علامت‌گذاری حل‌شده")
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)


class CrawlJobAdmin(admin.ModelAdmin):
    list_display = ("start_url", "status", "max_pages", "pages_found",
                    "pages_indexed", "pages_failed", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("log", "error_message", "created_at", "updated_at")


admin_site.register(WidgetConfig, WidgetConfigAdmin)
admin_site.register(ProviderSettings, ProviderSettingsAdmin)
admin_site.register(Document, DocumentAdmin)
admin_site.register(AnalyticsEvent, AnalyticsEventAdmin)
admin_site.register(AdminNotification, AdminNotificationAdmin)
admin_site.register(get_user_model(), UserAdmin)
admin_site.register(Group)
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Feedback, FeedbackAdmin)
admin_site.register(Lead, LeadAdmin)
admin_site.register(HandoffRequest, HandoffRequestAdmin)
admin_site.register(UnansweredQuestion, UnansweredQuestionAdmin)
admin_site.register(CrawlJob, CrawlJobAdmin)


@admin.register(BusinessRule, site=admin_site)
class BusinessRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "priority", "trigger_type", "trigger_value", "action_type", "action_label", "updated_at")
    list_filter = ("enabled", "trigger_type", "action_type")
    list_editable = ("enabled", "priority")
    search_fields = ("name", "trigger_value", "action_payload", "action_label")
