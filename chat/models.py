import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models

from .encrypted_fields import EncryptedCharField


def generate_public_key():
    return uuid.uuid4().hex


def generate_conversation_id():
    return uuid.uuid4().hex


# Shared intent taxonomy used by messages, conversations and analytics.
INTENT_GENERAL = "general"
INTENT_SUPPORT = "support"
INTENT_PURCHASE = "purchase"
INTENT_PRICING = "pricing"
INTENT_COMPLAINT = "complaint"
INTENT_ORDER_TRACKING = "order_tracking"
INTENT_CONTACT_REQUEST = "contact_request"
INTENT_GREETING = "greeting"

INTENT_CHOICES = (
    (INTENT_GENERAL, "General / information"),
    (INTENT_SUPPORT, "Support"),
    (INTENT_PURCHASE, "Purchase"),
    (INTENT_PRICING, "Pricing"),
    (INTENT_COMPLAINT, "Complaint"),
    (INTENT_ORDER_TRACKING, "Order tracking"),
    (INTENT_CONTACT_REQUEST, "Contact request"),
    (INTENT_GREETING, "Greeting"),
)


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

    # Human handoff — Telegram bot (token is a secret, encrypted at rest)
    telegram_bot_token = EncryptedCharField(max_length=1024, blank=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True)

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
    # Which widget bundle to serve: classic / onyx (professional) / linen (modern).
    # The file is chosen by the installation snippet and the live preview.
    widget_theme = models.CharField(
        max_length=20,
        choices=(
            ("classic", "کلاسیک — سبک و پایدار"),
            ("onyx", "حرفه‌ای (Onyx) — تیره و پرمیوم"),
            ("linen", "مدرن (Linen) — روشن و مینیمال"),
        ),
        default="classic",
        help_text="نسخه‌ی رابط کاربری ویجت. هر سه از یک تنظیمات شخصی‌سازی استفاده می‌کنند.",
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

    # Streaming answers (SSE with automatic non-streaming fallback).
    enable_streaming = models.BooleanField(
        default=True,
        help_text="Stream AI answers token-by-token (SSE) with automatic fallback.",
    )

    # Citation / source display under AI answers.
    show_citations = models.BooleanField(
        default=True,
        help_text="Show source chips (document titles / page links) under AI answers.",
    )

    # Lead capture — collect name + email/phone from interested visitors.
    enable_lead_capture = models.BooleanField(
        default=True,
        help_text="Offer an in-widget lead form (email/telegram/whatsapp handoff UIs use it too).",
    )
    lead_form_title = models.CharField(max_length=200, default="برای پیگیری، راه تماس بگذارید")
    lead_form_description = models.CharField(
        max_length=400,
        default="کارشناس ما در اسرع وقت با شما تماس می‌گیرد.",
    )

    # Human handoff channels.
    enable_handoff = models.BooleanField(
        default=True,
        help_text="Offer human handoff when the assistant cannot resolve an issue.",
    )
    handoff_email = models.EmailField(blank=True, help_text="Fallback email for handoff/lead notifications.")
    handoff_telegram_url = models.URLField(max_length=500, blank=True, help_text="e.g. https://t.me/yourteam")
    handoff_whatsapp_url = models.URLField(max_length=500, blank=True, help_text="e.g. https://wa.me/98912...")
    handoff_contact_url = models.URLField(max_length=500, blank=True, help_text="Site contact form URL")
    handoff_message = models.TextField(
        default="پاسخ این سؤال در دانش دستیار نبود؛ یک کارشناس انسانی بررسی می‌کند.",
    )
    handoff_trigger = models.CharField(
        max_length=20,
        choices=(
            ("always", "Always show handoff option"),
            ("low_confidence", "Only on low-confidence / fallback answers"),
            ("off", "Never (disable handoff UI)"),
        ),
        default="low_confidence",
    )

    enable_conversation_memory = models.BooleanField(
        default=True,
        help_text="When disabled, the model gets no history (each turn stateless). When enabled, context_window controls how much history.",
    )
    context_window = models.PositiveSmallIntegerField(
        default=6,
        help_text="How many previous messages are included as conversation context (0-20). Ignored when memory is disabled.",
    )
    temperature = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.60,
    )
    model_name = models.CharField(max_length=120, blank=True)
    system_prompt = models.TextField(blank=True)
    user_prompt = models.TextField(blank=True)

    # ── Prompt builder (feature: tone/name/business context) ─────────────
    # If prompt_mode == "auto", system_prompt is generated from the builder
    # fields; if "manual", the raw system_prompt is used as-is. The panel
    # shows both interfaces side-by-side and the builder never overwrites a
    # manual edit without confirmation — this satisfies "both, if possible".
    prompt_mode = models.CharField(
        max_length=10,
        choices=(("auto", "سازنده هوشمند"), ("manual", "ویرایش دستی")),
        default="auto",
    )
    prompt_tone = models.CharField(
        max_length=20,
        choices=(
            ("friendly", "دوستانه و صمیمی"),
            ("formal", "رسمی و حرفه‌ای"),
            ("concise", "مختصر و مستقیم"),
            ("playful", "شوخ و خلاق"),
            ("supportive", "حمایتی و همدل"),
        ),
        default="friendly",
    )
    prompt_assistant_name = models.CharField(max_length=60, blank=True, default="دستیار هوشمند")
    prompt_business_context = models.TextField(
        blank=True,
        help_text="معرفی کوتاه کسب‌وکار: چه می‌فروشید، مخاطب کیست، چه لحنی مناسب است. سازنده از همین متن پرامپت حرفه‌ای می‌سازد.",
    )
    prompt_language = models.CharField(
        max_length=20,
        choices=(("fa", "فارسی"), ("en", "English"), ("auto", "خودکار (FA/EN)")),
        default="fa",
    )
    prompt_use_emoji = models.BooleanField(default=True)
    prompt_answer_length = models.CharField(
        max_length=20,
        choices=(("short", "کوتاه"), ("balanced", "متعادل"), ("detailed", "مفصل و توضیحی")),
        default="balanced",
    )
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

    def effective_system_prompt(self):
        """Return the system prompt the LLM should actually receive.

        Manual mode: the raw system_prompt (if non-empty) wins.
        Auto mode: a professionally-structured prompt is composed from the
        builder fields + the business context. Either way the result is a
        safe, RAG-aware system instruction.
        """
        if self.prompt_mode == "manual" and (self.system_prompt or "").strip():
            return self.system_prompt.strip()
        return build_auto_system_prompt(self)

    def __str__(self):
        return f"{self.business_name} widget settings"


# ── Prompt builder helper (kept here to avoid circular imports) ──────────
def build_auto_system_prompt(config):
    """Compose a high-quality system prompt from widget/business context."""
    name = (getattr(config, "prompt_assistant_name", "") or "").strip() or "دستیار هوشمند"
    business = (getattr(config, "prompt_business_context", "") or "").strip()
    tone = getattr(config, "prompt_tone", "friendly")
    lang = getattr(config, "prompt_language", "fa")
    use_emoji = bool(getattr(config, "prompt_use_emoji", True))
    length = getattr(config, "prompt_answer_length", "balanced")

    tone_map = {
        "friendly": "صمیمی، گرم و دوستانه اما حرفه‌ای",
        "formal": "رسمی، دقیق و حرفه‌ای",
        "concise": "مختصر، مستقیم و بدون حاشیه",
        "playful": "شوخ‌طبع و خلاق اما محترمانه",
        "supportive": "همدل، حمایتی و اطمینان‌بخش",
    }
    length_map = {
        "short": "پاسخ‌ها کوتاه و خلاصه باشد.",
        "balanced": "پاسخ‌ها متعادل: کامل اما بدون اطاله.",
        "detailed": "پاسخ‌ها مفصل، با جزئیات و مثال در صورت نیاز.",
    }
    lang_map = {
        "fa": "زبان پیش‌فرض فارسی است.",
        "en": "Default language is English.",
        "auto": "به زبان کاربر (فارسی یا انگلیسی) پاسخ بده.",
    }
    parts = [
        f"تو «{name}» هستی — دستیار هوشمند همین سایت.",
        f"لحن تو {tone_map.get(tone, tone_map['friendly'])} است.",
        lang_map.get(lang, lang_map["fa"]),
        length_map.get(length, length_map["balanced"]),
        "فقط بر اساس متن منابع و گفت‌وگوی مجاز پاسخ بده، حدس نزن، و اگر اطلاعات کافی نیست شفاف اعلام کن.",
    ]
    if business:
        parts.insert(1, f"کسب‌وکار: {business[:600]}")
    if not use_emoji:
        parts.append("از ایموجی استفاده نکن.")
    parts.append(
        "اگر کاربر خارج از موضوع سایت سؤال کرد، مؤدبانه به موضوع اصلی برگرد."
    )
    return " ".join(parts)


class Document(models.Model):
    STATUS_CHOICES = (
        ("uploaded", "Uploaded"),
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    )
    SOURCE_CHOICES = (
        ("upload", "Upload"),
        ("crawl", "Crawl"),
    )
    FILE_TYPE_CHOICES = (
        ("pdf", "PDF"),
        ("txt", "Text"),
        ("docx", "Word"),
    )

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/%Y/%m/", blank=True)
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        blank=True,
    )
    # Crawled pages carry their text inline instead of an uploaded file.
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default="upload",
    )
    source_url = models.URLField(max_length=1000, blank=True)
    source_text = models.TextField(blank=True)
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


class CrawlJob(models.Model):
    """A website crawl request created from the admin panel.

    The manager enters the site URL; the system crawls same-domain pages
    (with SSRF protection), converts each page to a knowledge Document and
    queues embedding. A failed page never aborts the whole job.

    The "simple mode" the operator asked for is a single textarea where
    the manager pastes one URL per line; the view fans out one CrawlJob
    per line so each host is crawled independently (no cross-host leakage).
    """

    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed"),
    )

    start_url = models.URLField(max_length=1000)
    # Kept for list display; new jobs store the real limit here.
    max_pages = models.PositiveIntegerField(default=30)
    max_pages_per_url = models.PositiveIntegerField(default=30)
    crawl_mode = models.CharField(max_length=20, default="single")
    source_urls = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    pages_found = models.PositiveIntegerField(default=0)
    pages_indexed = models.PositiveIntegerField(default=0)
    pages_failed = models.PositiveIntegerField(default=0)
    log = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Crawl job"
        verbose_name_plural = "Crawl jobs"

    def __str__(self):
        return f"{self.start_url} ({self.status})"


class Conversation(models.Model):
    """A visitor conversation with the assistant."""

    STATUS_CHOICES = (
        ("open", "Open"),
        ("resolved", "Resolved"),
        ("handed_off", "Handed off"),
    )

    conversation_id = models.CharField(
        max_length=64,
        unique=True,
        default=generate_conversation_id,
        db_index=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    first_intent = models.CharField(max_length=40, blank=True)
    last_intent = models.CharField(max_length=40, blank=True)
    message_count = models.PositiveIntegerField(default=0)
    origin = models.CharField(max_length=300, blank=True)
    path = models.CharField(max_length=1000, blank=True)
    visitor_key = models.CharField(max_length=64, blank=True, db_index=True)
    lead = models.ForeignKey(
        "Lead",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        return self.conversation_id


class Message(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    intent = models.CharField(max_length=40, blank=True)
    # Stored as {"doc_id","document_title","document_id","score","url","page_number"}
    sources = models.JSONField(default=list, blank=True)
    used_fallback = models.BooleanField(default=False)
    confidence = models.FloatField(null=True, blank=True)
    # Token index of the last streamed assistant chunk (for resume-safe history)
    is_streamed = models.BooleanField(default=False)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=("conversation", "created_at"), name="msg_conv_created_idx"),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class Feedback(models.Model):
    """Per-message like/dislike with optional comment."""

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="feedback")
    helpful = models.BooleanField()
    comment = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"

    def __str__(self):
        return f"{'👍' if self.helpful else '👎'} message #{self.message_id}"


class Lead(models.Model):
    """A captured sales lead (name + contact channel) from the widget."""

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(
        max_length=20,
        choices=(
            ("widget_form", "Widget form"),
            ("handoff_email", "Handoff — email"),
            ("handoff_telegram", "Handoff — Telegram"),
            ("handoff_whatsapp", "Handoff — WhatsApp"),
            ("handoff_contact", "Handoff — contact form"),
        ),
        default="widget_form",
    )
    note = models.TextField(blank=True)
    origin = models.CharField(max_length=300, blank=True)
    conversation = models.ForeignKey(
        Conversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return f"{self.name} ({self.email or self.phone})"


class HandoffRequest(models.Model):
    """A request for human support escalated from the widget."""

    STATUS_CHOICES = (
        ("new", "New"),
        ("in_progress", "In progress"),
        ("done", "Done"),
    )

    CHANNEL_CHOICES = (
        ("email", "Email"),
        ("telegram", "Telegram"),
        ("whatsapp", "WhatsApp"),
        ("contact_form", "Site contact form"),
    )

    conversation = models.ForeignKey(
        Conversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="handoff_requests",
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    question = models.TextField(blank=True, help_text="The visitor's last question that triggered handoff.")
    notified = models.BooleanField(default=False)
    origin = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Handoff request"
        verbose_name_plural = "Handoff requests"

    def __str__(self):
        return f"{self.channel} — {self.created_at:%Y-%m-%d %H:%M}"


class BusinessRule(models.Model):
    """If-this-then-that rules the operator defines from the panel.

    The product promise: a site manager with no ML knowledge can say
    "if the visitor asks about pricing, suggest /pricing" or
    "if they're angry, offer human handoff" — and it actually fires.
    Rules are evaluated on every turn *before* the LLM call; matching
    rules attach a non-blocking ``rule_action`` to the response that the
    widget renders as a suggestion chip / handoff nudge. Nothing here
    replaces the LLM — it augments it.

    Triggers (AND within a rule is implicit — any trigger match fires):
      intent  — one of the INTENT_CHOICES (or empty = any intent)
      keyword — substring in the normalized user message
      sentiment — coarse negative/angry detector
      fallback — only when the answer would have been a fallback

    Actions:
      suggest_link  — payload is a URL the widget shows as a chip
      suggest_text  — payload is a short text suggestion
      handoff       — payload is a channel hint (the widget's handoff bar)
      note: payload is stored as plain text; URL validation happens in clean().
    """

    TRIGGER_CHOICES = (
        ("intent", "نیت (intent)"),
        ("keyword", "کلیدواژه"),
        ("sentiment_negative", "لحن منفی / عصبانیت"),
        ("fallback", "فقط هنگام بی‌پاسخی"),
    )
    ACTION_CHOICES = (
        ("suggest_link", "پیشنهاد لینک"),
        ("suggest_text", "پیشنهاد متن"),
        ("handoff", "اتصال به کارشناس"),
    )

    name = models.CharField(max_length=120, help_text="نام داخلی قانون، مثلا «قیمت → صفحه محصولات»")
    enabled = models.BooleanField(default=True, db_index=True)
    priority = models.PositiveSmallIntegerField(default=100, help_text="عدد کمتر = اولویت بالاتر")
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    trigger_value = models.CharField(max_length=200, blank=True, help_text="برای intent: کد intent؛ برای keyword: عبارت؛ برای sentiment/fallback خالی بگذارید")
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_payload = models.CharField(max_length=1000, blank=True, help_text="برای link: URL؛ برای text: متن پیشنهادی؛ برای handoff: توضیح کوتاه")
    action_label = models.CharField(max_length=80, blank=True, help_text="متن دکمه/چیپ که کاربر می‌بیند")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("priority", "-updated_at")
        verbose_name = "Business rule"
        verbose_name_plural = "Business rules"

    def clean(self):
        if self.trigger_type == "intent" and self.trigger_value:
            valid = {c[0] for c in INTENT_CHOICES}
            if self.trigger_value not in valid:
                raise ValidationError({"trigger_value": f"intent نامعتبر: {self.trigger_value!r}"})
        if self.action_type == "suggest_link" and self.action_payload:
            if not self.action_payload.startswith(("http://", "https://", "/")):
                raise ValidationError({"action_payload": "لینک باید با http(s):// یا / شروع شود."})

    def __str__(self):
        state = "✓" if self.enabled else "○"
        return f"{state} {self.name} [{self.get_trigger_type_display()} → {self.get_action_type_display()}]"


class UnansweredQuestion(models.Model):
    """A question the assistant could not answer confidently.

    Raised when retrieval finds nothing or the model answered with the
    controlled fallback. Powers the admin panel "what do visitors ask that
    our knowledge base is missing" view.
    """

    question = models.CharField(max_length=2000, db_index=True)
    question_hash = models.CharField(max_length=64, db_index=True)
    count = models.PositiveIntegerField(default=1)
    reason = models.CharField(
        max_length=20,
        choices=(
            ("no_context", "No matching context"),
            ("low_confidence", "Low-confidence answer"),
            ("model_fallback", "Model declared it does not know"),
        ),
        default="low_confidence",
    )
    last_intent = models.CharField(max_length=40, blank=True)
    conversation = models.ForeignKey(
        Conversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unanswered_questions",
    )
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-count", "-updated_at")
        verbose_name = "Unanswered question"
        verbose_name_plural = "Unanswered questions"

    def __str__(self):
        return self.question[:80]


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
