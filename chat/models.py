import uuid

from django.db import models


def generate_public_key():
    return uuid.uuid4().hex


class Site(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    public_key = models.CharField(
        max_length=32,
        unique=True,
        default=generate_public_key,
        editable=False,
    )
    domain = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class WidgetConfig(models.Model):
    site = models.OneToOneField(
        Site,
        on_delete=models.CASCADE,
        related_name="widget_config",
    )
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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Widget config: {self.site.name}"


class Conversation(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="conversations",
    )
    external_id = models.CharField(max_length=100)
    page_url = models.URLField(max_length=1000, blank=True)
    referrer = models.URLField(max_length=1000, blank=True)
    user_agent = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_activity_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("site", "external_id"),
                name="unique_conversation_per_site",
            ),
        ]

    def __str__(self):
        return f"{self.site.slug} / {self.external_id}"


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

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="analytics_events",
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

    def __str__(self):
        return f"{self.site.slug}: {self.event_type}"
