import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models

from .encrypted_fields import EncryptedCharField


def generate_public_key():
    return uuid.uuid4().hex


class ProviderSettings(models.Model):
    """Admin-managed LLM / embedding provider configuration.

    Values here override environment variables. API keys are encrypted at
    rest with a key derived from SECRET_KEY. Blank values fall back to the
    matching environment variable.
    """

    singleton_key = models.PositiveSmallIntegerField(
        default=1,
        unique=True,
        editable=False,
    )

    llm_api_key = EncryptedCharField(max_length=1024, blank=True)
    llm_base_url = models.CharField(max_length=500, blank=True)
    llm_model = models.CharField(max_length=120, blank=True)
    llm_max_tokens = models.PositiveIntegerField(null=True, blank=True)
    llm_timeout_seconds = models.PositiveIntegerField(null=True, blank=True)
    llm_max_retries = models.PositiveIntegerField(null=True, blank=True)

    embedding_api_key = EncryptedCharField(max_length=1024, blank=True)
    embedding_base_url = models.CharField(max_length=500, blank=True)
    embedding_model = models.CharField(max_length=120, blank=True)
    embedding_timeout_seconds = models.PositiveIntegerField(null=True, blank=True)
    embedding_max_retries = models.PositiveIntegerField(null=True, blank=True)

    rag_max_concurrent = models.PositiveIntegerField(null=True, blank=True)
    response_cache_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Widget installation / access control
    widget_public_key = models.CharField(max_length=200, blank=True)
    widget_allowed_origins = models.TextField(
        blank=True,
        help_text="One origin per line, e.g. https://example.com",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI provider settings"
        verbose_name_plural = "AI provider settings"

    @property
    def allowed_origins_list(self):
        origins = []
        for part in re.split(r"[\n,]+", self.widget_allowed_origins or ""):
            origin = part.strip().rstrip("/")
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    def clean(self):
        if ProviderSettings.objects.exclude(pk=self.pk).exists():
            raise ValidationError(
                "Only one provider settings record is allowed."
            )
        if self.widget_public_key and any(
            character.isspace() for character in self.widget_public_key
        ):
            raise ValidationError(
                "The widget public key must not contain whitespace."
            )
        for origin in self.allowed_origins_list:
            if not origin.startswith(("http://", "https://")):
                raise ValidationError(
                    f"Invalid origin: {origin!r}. It must start with "
                    "http:// or https://."
                )

    def save(self, *args, **kwargs):
        if self.widget_allowed_origins:
            self.widget_allowed_origins = "\n".join(self.allowed_origins_list)
        super().save(*args, **kwargs)

    def __str__(self):
        return "AI provider settings"


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
    header_badge = models.CharField(max_length=40, default="ONLINE")
    bot_avatar_text = models.CharField(max_length=8, default="AI")
    input_placeholder = models.CharField(
        max_length=120,
        default="سؤال خود را بنویسید...",
    )
    theme_mode = models.CharField(
        max_length=20,
        choices=(
            ("gradient", "Gradient"),
            ("solid", "Solid"),
            ("glass", "Glass"),
        ),
        default="gradient",
    )
    dark_mode = models.CharField(
        max_length=10,
        choices=(
            ("auto", "Auto (system)"),
            ("light", "Light"),
            ("dark", "Dark"),
        ),
        default="auto",
    )
    accent_color = models.CharField(max_length=20, default="#a78bfa")
    panel_width = models.PositiveIntegerField(default=400)
    panel_height = models.PositiveIntegerField(default=640)
    border_radius = models.PositiveIntegerField(default=24)
    mobile_fullscreen = models.BooleanField(default=True)
    logo_url = models.URLField(max_length=1000, blank=True)
    font_family = models.CharField(
        max_length=200,
        default="'Vazirmatn', 'Inter', 'IRANSansX', ui-sans-serif, system-ui, sans-serif",
    )
    font_size = models.CharField(
        max_length=10,
        choices=(
            ("small", "Small"),
            ("normal", "Normal"),
            ("large", "Large"),
        ),
        default="normal",
    )
    bubble_style = models.CharField(
        max_length=10,
        choices=(
            ("rounded", "Rounded"),
            ("sharp", "Sharp"),
            ("pill", "Pill"),
        ),
        default="rounded",
    )
    position = models.CharField(
        max_length=20,
        choices=(
            ("bottom-right", "Bottom right"),
            ("bottom-left", "Bottom left"),
            ("top-right", "Top right"),
            ("top-left", "Top left"),
        ),
        default="bottom-right",
    )
    position_vertical_offset = models.PositiveIntegerField(
        default=24,
        help_text="Distance from top/bottom edge in pixels",
    )
    position_horizontal_offset = models.PositiveIntegerField(
        default=24,
        help_text="Distance from left/right edge in pixels",
    )
    icon_type = models.CharField(
        max_length=10,
        choices=(
            ("default", "Default icon"),
            ("custom", "Custom icon upload"),
        ),
        default="default",
    )
    default_icon_choice = models.CharField(
        max_length=30,
        choices=(
            ("chat-bubble", "Chat bubble 💬"),
            ("message-circle", "Message circle 📩"),
            ("robot", "Robot 🤖"),
            ("headset", "Headset 🎧"),
            ("sparkle", "Sparkle ✨"),
            ("lightning", "Lightning ⚡"),
        ),
        default="chat-bubble",
    )
    custom_icon_file = models.FileField(
        upload_to="widget-icons/",
        blank=True,
        help_text="Upload a PNG or SVG file (max 200KB)",
    )
    show_feedback = models.BooleanField(default=True)
    show_powered_by = models.BooleanField(default=True)
    show_timestamp = models.BooleanField(default=True)
    show_avatar = models.BooleanField(default=True)
    enable_sounds = models.BooleanField(default=False)
    enable_animations = models.BooleanField(default=True)
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


class AnalyticsEvent(models.Model):
    EVENT_CHOICES = (
        ("widget_loaded", "Widget loaded"),
        ("user_message", "User message"),
        ("assistant_answered", "Assistant answered"),
        ("answer_helpful", "Answer helpful"),
        ("answer_not_helpful", "Answer not helpful"),
        ("fallback_triggered", "Fallback triggered"),
        ("error_occurred", "Error occurred"),
        ("high_pressure", "High pressure detected"),
    )

    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    path = models.CharField(max_length=1000, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Analytics event"
        verbose_name_plural = "Analytics events"
        indexes = [
            models.Index(
                fields=("event_type", "created_at"),
                name="evt_type_created_idx",
            ),
        ]

    def __str__(self):
        return self.event_type


class AdminNotification(models.Model):
    """In-app notifications for admin panel alerts."""

    SEVERITY_CHOICES = (
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="warning",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.severity}] {self.title}"
