"""Panel forms (Persian labels) — ModelForms over WidgetConfig/ProviderSettings.

The customizer splits the very wide WidgetConfig into two forms
(appearance + behavior) so the panel page stays readable. All
appearance-affecting changes invalidate the widget-config cache in the
view after a successful save.
"""

from django import forms

from .models import CrawlJob, ProviderSettings, WidgetConfig


class WidgetAppearanceForm(forms.ModelForm):
    """Visual identity of the widget (colors, brand, position, icon)."""

    class Meta:
        model = WidgetConfig
        fields = (
            "widget_theme",
            "business_name",
            "website_url",
            "title",
            "subtitle",
            "greeting",
            "header_badge",
            "primary_color",
            "secondary_color",
            "accent_color",
            "logo_url",
            "bot_avatar_text",
            "font_family",
            "font_size",
            "theme_mode",
            "dark_mode",
            "bubble_style",
            "border_radius",
            "panel_width",
            "panel_height",
            "position",
            "position_vertical_offset",
            "position_horizontal_offset",
            "icon_type",
            "default_icon_choice",
            "custom_icon_file",
            "mobile_fullscreen",
        )
        widgets = {
            "greeting": forms.Textarea(attrs={"rows": 2}),
            "subtitle": forms.TextInput(),
        }


class WidgetBehaviorForm(forms.ModelForm):
    """Behavior: streaming, citations, lead capture, handoff, suggestions."""

    enable_conversation_memory = forms.BooleanField(
        label="حافظه مکالمه فعال باشد (ضمیرها و «مشخصاتش؟» را بفهمد)",
        required=False,
        help_text="خاموش = هر سؤال جدا (بدون زمینه). روشن = پیام‌های قبلی به مدل داده می‌شود.",
    )
    context_window = forms.IntegerField(
        label="عمق حافظه — تعداد پیام‌های قبلی",
        required=False, min_value=0, max_value=20,
        help_text="وقتی حافظه روشن است استفاده می‌شود. ۰ = بدون حافظه، ۴-۸ پیشنهادی.",
    )
    suggestions_text = forms.CharField(
        label="سؤال‌های پیشنهادی (هر سطر یک سؤال)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="در ابتدای مکالمه به‌عنوان چیپ‌های قابل کلیک نمایش داده می‌شوند.",
    )

    class Meta:
        model = WidgetConfig
        fields = (
            "input_placeholder",
            "show_powered_by",
            "show_timestamp",
            "show_avatar",
            "show_feedback",
            "enable_sounds",
            "enable_animations",
            "enable_streaming",
            "show_citations",
            "enable_conversation_memory",
            "context_window",
            "faq_url",
            "privacy_url",
            "support_email",
            "enable_lead_capture",
            "lead_form_title",
            "lead_form_description",
            "enable_handoff",
            "handoff_trigger",
            "handoff_message",
            "handoff_email",
            "handoff_telegram_url",
            "handoff_whatsapp_url",
            "handoff_contact_url",
        )
        widgets = {
            "lead_form_description": forms.Textarea(attrs={"rows": 2}),
            "handoff_message": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            suggestions = self.instance.suggestions or []
            self.fields["suggestions_text"].initial = "\n".join(
                str(s) for s in suggestions
            )
            if self.instance.context_window is not None:
                self.fields["context_window"].initial = self.instance.context_window
            if self.instance.enable_conversation_memory is not None:
                self.fields["enable_conversation_memory"].initial = self.instance.enable_conversation_memory

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get("suggestions_text", "")
        suggestions = [
            line.strip()[:120]
            for line in raw.splitlines()
            if line.strip()
        ][:8]
        instance.suggestions = suggestions
        # Explicit context_window (None means keep default)
        cw = self.cleaned_data.get("context_window")
        if cw is not None:
            instance.context_window = max(0, min(20, int(cw)))
        if commit:
            instance.save()
        return instance


class InstallationForm(forms.ModelForm):
    """Widget installation: public key + allowed origins."""

    widget_allowed_origins = forms.CharField(
        label="دامنه‌های مجاز (هر خط یک دامنه)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "dir": "ltr"}),
        help_text="مثال: https://example.com — Wildcard هم پذیرفته می‌شود: https://*.example.com",
    )

    class Meta:
        model = ProviderSettings
        fields = ("widget_public_key", "widget_allowed_origins")
        widgets = {
            "widget_public_key": forms.TextInput(attrs={"dir": "ltr"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["widget_allowed_origins"].initial = "\n".join(
                self.instance.allowed_origins_list
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.widget_allowed_origins = self.cleaned_data.get(
            "widget_allowed_origins", ""
        )
        if commit:
            instance.save()
        return instance


class AIProviderForm(forms.ModelForm):
    """LLM / embedding provider credentials (encrypted at rest)."""

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
            "telegram_bot_token",
            "telegram_chat_id",
        )
        widgets = {
            "llm_api_key": forms.PasswordInput(
                attrs={"dir": "ltr", "autocomplete": "new-password"},
                render_value=False,
            ),
            "embedding_api_key": forms.PasswordInput(
                attrs={"dir": "ltr", "autocomplete": "new-password"},
                render_value=False,
            ),
            "telegram_bot_token": forms.PasswordInput(
                attrs={"dir": "ltr", "autocomplete": "new-password"},
                render_value=False,
            ),
            "llm_base_url": forms.TextInput(attrs={"dir": "ltr"}),
            "embedding_base_url": forms.TextInput(attrs={"dir": "ltr"}),
        }

    def save(self, commit=True):  # keep existing secret when field left blank
        instance = super().save(commit=False)
        for field in ("llm_api_key", "embedding_api_key", "telegram_bot_token"):
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


class CrawlStartForm(forms.ModelForm):
    """Start a website crawl — now multi-URL.

    The non-technical operator pastes one URL per line; the view fans
    out one CrawlJob per line so each host is crawled independently.
    Single-URL submissions keep working.
    """

    crawl_urls = forms.CharField(
        label="لینک‌ها (هر خط یکی)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "dir": "ltr", "placeholder": "https://example.com\nhttps://example.com/blog", "id": "kb-crawl-urls"}),
        help_text="هر خط یک لینک. هر لینک جداگانه خزیده می‌شود؛ دامنه‌های مختلف مشکلی ندارند.",
    )

    class Meta:
        model = CrawlJob
        fields = ("start_url", "max_pages")
        widgets = {
            "start_url": forms.URLInput(attrs={"dir": "ltr", "placeholder": "https://example.com", "id": "kb-crawl-start-url"}),
            "max_pages": forms.NumberInput(attrs={"id": "kb-crawl-max-pages"}),
        }
        labels = {
            "start_url": "آدرس سایت",
            "max_pages": "حداکثر تعداد صفحات",
        }
        help_texts = {
            "start_url": "فقط دامنه‌ی همین سایت خزیده می‌شود؛ لینک‌های بیرونی نادیده گرفته می‌شوند.",
            "max_pages": "بین ۱ تا ۲۰۰ صفحه — برای حالت چندلینکی، این سقف برای هر لینک جداگانه اعمال می‌شود.",
        }

    def clean(self):
        cleaned = super().clean()
        # Prefer the textarea when it has content; otherwise keep start_url.
        raw_urls = (cleaned.get("crawl_urls") or "").strip()
        if raw_urls:
            urls = [u.strip() for u in raw_urls.splitlines() if u.strip()]
            # Basic validation: must look like http(s)
            bad = [u for u in urls if not u.startswith(("http://", "https://"))]
            if bad:
                self.add_error("crawl_urls", f"این لینک‌ها باید با http(s):// شروع شوند: {', '.join(bad[:3])}")
            cleaned["_parsed_urls"] = urls
        else:
            # Single-URL fallback via start_url
            single = (cleaned.get("start_url") or "").strip()
            if single:
                cleaned["_parsed_urls"] = [single]
            else:
                cleaned["_parsed_urls"] = []
        return cleaned

    def clean_max_pages(self):
        value = self.cleaned_data.get("max_pages") or 30
        return max(1, min(200, value))


class KnowledgeUploadForm(forms.Form):
    """In-panel document upload — no round-trip to /admin/.

    The knowledge page asked for "a manager without any knowledge can
    upload easily"; a dedicated upload form in the panel is the fix.
    """

    title = forms.CharField(label="عنوان سند", max_length=255, required=False, help_text="خالی بگذارید تا از نام فایل استفاده شود.")
    file = forms.FileField(label="فایل", help_text="PDF، DOCX یا TXT — تا ۲۵ مگابایت")
    file2 = forms.FileField(label="فایل دوم (اختیاری)", required=False)
    file3 = forms.FileField(label="فایل سوم (اختیاری)", required=False)

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            from .document_pipeline import detect_file_type, MAX_DOCUMENT_BYTES
            if not detect_file_type(f.name):
                raise forms.ValidationError("فرمت مجاز فقط PDF، TXT و DOCX است.")
            if f.size > MAX_DOCUMENT_BYTES:
                raise forms.ValidationError("حجم فایل نباید بیشتر از ۲۵ مگابایت باشد.")
        return f

    def _check_optional(self, name):
        f = self.cleaned_data.get(name)
        if f:
            from .document_pipeline import detect_file_type, MAX_DOCUMENT_BYTES
            if not detect_file_type(f.name):
                raise forms.ValidationError("فرمت مجاز فقط PDF، TXT و DOCX است.")
            if f.size > MAX_DOCUMENT_BYTES:
                raise forms.ValidationError("حجم فایل نباید بیشتر از ۲۵ مگابایت باشد.")
        return f

    def clean_file2(self):
        return self._check_optional("file2")

    def clean_file3(self):
        return self._check_optional("file3")


class PromptBuilderForm(forms.ModelForm):
    """Dual-mode prompt editor: builder knobs + raw textareas."""

    class Meta:
        model = WidgetConfig
        fields = (
            "prompt_mode",
            "prompt_tone",
            "prompt_assistant_name",
            "prompt_business_context",
            "prompt_language",
            "prompt_use_emoji",
            "prompt_answer_length",
            "system_prompt",
            "user_prompt",
            "temperature",
            "model_name",
        )
        widgets = {
            "prompt_business_context": forms.Textarea(attrs={"rows": 3, "placeholder": "مثلا: فروشگاه لوازم آرایشی، مخاطب خانم‌های ۱۸-۳۵، لحن صمیمی…"}),
            "system_prompt": forms.Textarea(attrs={"rows": 6, "dir": "ltr"}),
            "user_prompt": forms.Textarea(attrs={"rows": 4, "dir": "ltr"}),
        }


class BusinessRuleForm(forms.ModelForm):
    class Meta:
        model = __import__("chat.models", fromlist=["BusinessRule"]).BusinessRule
        fields = ("name", "enabled", "priority", "trigger_type", "trigger_value", "action_type", "action_payload", "action_label")
        widgets = {
            "trigger_value": forms.TextInput(attrs={"dir": "ltr", "placeholder": "intent code / keyword"}),
            "action_payload": forms.TextInput(attrs={"dir": "ltr", "placeholder": "https://... or text"}),
        }
