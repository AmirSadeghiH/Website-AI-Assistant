import uuid

from django.core.exceptions import ValidationError
from django.db import models


def generate_public_key():
    # Kept for the historical 0001 migration; multi-site no longer uses it.
    return uuid.uuid4().hex


class WidgetConfig(models.Model):
    singleton_key = models.PositiveSmallIntegerField(
        default=1,
        unique=True,
        editable=False,
    )
    business_name = models.CharField(max_length=200, default="AI Support")
    website_url = models.URLField(max_length=1000, blank=True)
    title = models.CharField(max_length=120, default="دستیار هوش مصنوعی")
    subtitle = models.CharField(
        max_length=200,
        default="پاسخ‌های فوری به سوالات شما",
    )
    greeting = models.TextField(
        default="سلام! 👋 چطور می‌توانم کمکتان کنم؟",
    )
    primary_color = models.CharField(max_length=20, default="#5048E5")
    secondary_color = models.CharField(max_length=20, default="#7C3AED")
    font_family = models.CharField(
        max_length=120,
        default="Inter, ui-sans-serif, system-ui, sans-serif",
    )
    position = models.CharField(
        max_length=20,
        choices=(
            ("bottom-right", "Bottom right"),
            ("bottom-left", "Bottom left"),
        ),
        default="bottom-right",
    )
    show_history = models.BooleanField(default=True)
    allow_feedback = models.BooleanField(default=True)
    show_powered_by = models.BooleanField(default=True)
    suggestions = models.JSONField(default=list, blank=True)
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.60,
    )
    model_name = models.CharField(max_length=120, blank=True)
    system_prompt = models.TextField(blank=True)
    user_prompt = models.TextField(blank=True)
    faq_url = models.URLField(max_length=1000, blank=True)
    privacy_url = models.URLField(max_length=1000, blank=True)
    support_email = models.EmailField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Widget settings"
        verbose_name_plural = "Widget settings"

    def clean(self):
        if WidgetConfig.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one widget settings record is allowed.")

    def __str__(self):
        return f"{self.business_name} widget settings"


class Document(models.Model):
    STATUS_CHOICES = (
        ("uploaded", "Uploaded"),
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    )
    FILE_TYPE_CHOICES = (
        ("pdf", "PDF"),
        ("txt", "Text"),
        ("docx", "Word"),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/")
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded",
    )
    error_message = models.TextField(blank=True)
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)
    chunk_count = models.PositiveIntegerField(default=0)
    embedding_count = models.PositiveIntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Knowledge document"
        verbose_name_plural = "Knowledge documents"

    def __str__(self):
        return self.title


class Conversation(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    page_url = models.URLField(max_length=1000, blank=True)
    referrer = models.URLField(max_length=1000, blank=True)
    user_agent = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_activity_at",)
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return self.external_id


class Message(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    )
    FEEDBACK_CHOICES = (
        ("helpful", "Helpful"),
        ("not_helpful", "Not helpful"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    feedback = models.CharField(
        max_length=20,
        choices=FEEDBACK_CHOICES,
        blank=True,
    )
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"


class AnalyticsEvent(models.Model):
    EVENT_CHOICES = (
        ("widget_loaded", "Widget loaded"),
        ("conversation_started", "Conversation started"),
        ("user_message", "User message"),
        ("assistant_answered", "Assistant answered"),
        ("answer_helpful", "Answer helpful"),
        ("answer_not_helpful", "Answer not helpful"),
        ("human_requested", "Human requested"),
        ("ticket_created", "Ticket created"),
        ("fallback_triggered", "Fallback triggered"),
        ("conversation_archived", "Conversation archived"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_events",
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    path = models.CharField(max_length=1000, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Analytics event"
        verbose_name_plural = "Analytics events"

    def __str__(self):
        return self.event_type
