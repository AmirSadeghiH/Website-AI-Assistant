"""Custom admin panel (/panel/) — the product control room.

Sits on top of Django session auth (``staff_member_required``) and Django
CSRF: no separate auth system, no API tokens in the browser. The Django
admin remains available for deep technical CRUD.
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .crawler import enqueue_crawl_job
from .document_pipeline import enqueue_document
from .forms import (
    AIProviderForm,
    CrawlStartForm,
    InstallationForm,
    WidgetAppearanceForm,
    WidgetBehaviorForm,
)
from .models import (
    AnalyticsEvent,
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
    INTENT_CHOICES,
)

DAYS_CHOICES = ((7, "۷ روز"), (14, "۱۴ روز"), (30, "۳۰ روز"), (90, "۹۰ روز"))


def _period(days):
    try:
        days = max(1, min(180, int(days)))
    except (TypeError, ValueError):
        days = 30
    return days, timezone.now() - timedelta(days=days)


def _form_errors(form):
    """Flatten a form's errors into a single Persian message."""
    parts = []
    for field, errors in form.errors.items():
        parts.append("; ".join(str(e) for e in errors))
    return " — ".join(parts) or "خطای نامشخص در فرم."


# ─── Dashboard ────────────────────────────────────────────────────────────

@staff_member_required
def dashboard(request):
    days, cutoff = _period(request.GET.get("days", 30))

    conversations_total = Conversation.objects.count()
    conversations_period = Conversation.objects.filter(created_at__gte=cutoff).count()
    messages_period = Message.objects.filter(created_at__gte=cutoff).count()
    assistant_qs = Message.objects.filter(role="assistant", created_at__gte=cutoff)
    avg_latency = assistant_qs.aggregate(v=Avg("latency_ms"))["v"]

    resolved_count = Conversation.objects.filter(status="resolved").count()
    handoff_count = Conversation.objects.filter(status="handed_off").count()
    resolution_rate = (
        round(100 * resolved_count / conversations_total) if conversations_total else 0
    )

    feedback_qs = Feedback.objects.filter(created_at__gte=cutoff)
    fb_up = feedback_qs.filter(helpful=True).count()
    fb_down = feedback_qs.filter(helpful=False).count()
    satisfaction = round(100 * fb_up / (fb_up + fb_down)) if (fb_up + fb_down) else None

    leads_period = Lead.objects.filter(created_at__gte=cutoff).count()
    handoff_period = HandoffRequest.objects.filter(created_at__gte=cutoff).count()
    errors_period = AnalyticsEvent.objects.filter(
        event_type="error_occurred", created_at__gte=cutoff
    ).count()
    unanswered_open = UnansweredQuestion.objects.filter(is_resolved=False).count()

    # Message volume per day (chart)
    per_day = (
        Message.objects.filter(created_at__gte=cutoff)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )
    day_labels = [row["date"].strftime("%m-%d") for row in per_day]
    day_values = [row["total"] for row in per_day]

    # Intent distribution (chart)
    per_intent = (
        Message.objects.filter(role="user", created_at__gte=cutoff, intent__gt="")
        .values("intent")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    intent_labels = [dict(INTENT_CHOICES).get(r["intent"], r["intent"]) for r in per_intent]
    intent_values = [r["total"] for r in per_intent]

    # Fallbacks per day
    fallback_qs = (
        Message.objects.filter(used_fallback=True, created_at__gte=cutoff)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(total=Count("id"))
        .order_by("date")
    )
    fb_labels = [row["date"].strftime("%m-%d") for row in fallback_qs]
    fb_values = [row["total"] for row in fallback_qs]

    recent_conversations = Conversation.objects.prefetch_related("messages")[:8]
    top_unanswered = UnansweredQuestion.objects.filter(is_resolved=False)[:6]
    recent_leads = Lead.objects.all()[:5]
    docs_ready = Document.objects.filter(status="ready").count()
    docs_failed = Document.objects.filter(status="failed").count()

    return render(request, "panel/dashboard.html", {
        "days": days,
        "days_choices": DAYS_CHOICES,
        "conversations_total": conversations_total,
        "conversations_period": conversations_period,
        "messages_period": messages_period,
        "avg_latency": round(avg_latency) if avg_latency else None,
        "resolution_rate": resolution_rate,
        "satisfaction": satisfaction,
        "fb_up": fb_up,
        "fb_down": fb_down,
        "leads_period": leads_period,
        "handoff_period": handoff_period,
        "errors_period": errors_period,
        "unanswered_open": unanswered_open,
        "docs_ready": docs_ready,
        "docs_failed": docs_failed,
        "chart_labels": json.dumps(day_labels),
        "chart_values": json.dumps(day_values),
        "fallback_labels": json.dumps(fb_labels),
        "fallback_values": json.dumps(fb_values),
        "intent_labels": json.dumps(intent_labels, ensure_ascii=False),
        "intent_values": json.dumps(intent_values),
        "recent_conversations": recent_conversations,
        "top_unanswered": top_unanswered,
        "recent_leads": recent_leads,
        "nav": "dashboard",
    })


# ─── Conversations ────────────────────────────────────────────────────────

@staff_member_required
def conversations(request):
    days, cutoff = _period(request.GET.get("days", 30))
    status_filter = request.GET.get("status", "")
    intent_filter = request.GET.get("intent", "")
    query = (request.GET.get("q") or "").strip()

    qs = Conversation.objects.all()
    if status_filter in {"open", "resolved", "handed_off"}:
        qs = qs.filter(status=status_filter)
    if intent_filter:
        qs = qs.filter(last_intent=intent_filter)
    if query:
        qs = qs.filter(messages__content__icontains=query).distinct()
    if request.GET.get("days") != "all":
        qs = qs.filter(updated_at__gte=cutoff)

    page = max(1, int(request.GET.get("page", 1) or 1))
    page_size = 25
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    items = qs.prefetch_related("messages")[page_size * (page - 1): page_size * page]

    return render(request, "panel/conversations.html", {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "status_filter": status_filter,
        "intent_filter": intent_filter,
        "query": query,
        "days": request.GET.get("days", 30),
        "intent_choices": INTENT_CHOICES,
        "nav": "conversations",
    })


@staff_member_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation.objects.prefetch_related("messages"), pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in {"open", "resolved", "handed_off"}:
            conversation.status = new_status
            conversation.save(update_fields=("status", "updated_at"))
            messages.success(request, "وضعیت مکالمه به‌روزرسانی شد.")
        return redirect("panel:conversation-detail", pk=pk)
    intents = conversation.messages.values_list("intent", flat=True).exclude(intent="")
    return render(request, "panel/conversation_detail.html", {
        "conversation": conversation,
        "intents": dict(INTENT_CHOICES),
        "nav": "conversations",
    })


# ─── Unanswered questions ─────────────────────────────────────────────────

@staff_member_required
def unanswered(request):
    items = UnansweredQuestion.objects.all()
    if request.GET.get("filter") == "resolved":
        items = items.filter(is_resolved=True)
    else:
        items = items.filter(is_resolved=False)
    return render(request, "panel/unanswered.html", {
        "items": items,
        "filter": request.GET.get("filter", "open"),
        "nav": "unanswered",
    })


@staff_member_required
@require_POST
def unanswered_toggle(request, pk):
    row = get_object_or_404(UnansweredQuestion, pk=pk)
    row.is_resolved = not row.is_resolved
    row.save(update_fields=("is_resolved", "updated_at"))
    messages.success(request, "وضعیت سؤال به‌روزرسانی شد.")
    return redirect("panel:unanswered")


# ─── Leads ────────────────────────────────────────────────────────────────

@staff_member_required
def leads(request):
    items = Lead.objects.select_related("conversation").all()
    source = request.GET.get("source", "")
    if source:
        items = items.filter(source=source)
    return render(request, "panel/leads.html", {
        "items": items,
        "source": source,
        "nav": "leads",
    })


# ─── Handoff requests ─────────────────────────────────────────────────────

@staff_member_required
def handoff_requests(request):
    items = HandoffRequest.objects.select_related("conversation").all()
    return render(request, "panel/handoff.html", {"items": items, "nav": "handoff"})


@staff_member_required
@require_POST
def leads_update(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    action = request.POST.get("action", "")
    if action == "delete":
        lead.delete()
        messages.success(request, "سرنخ حذف شد.")
    else:
        messages.error(request, "عملیات نامعتبر.")
    return redirect("panel:leads")


@staff_member_required
@require_POST
def handoff_update(request, pk):
    handoff = get_object_or_404(HandoffRequest, pk=pk)
    action = request.POST.get("action", "")
    if action == "progress":
        handoff.status = "in_progress"
        handoff.save(update_fields=("status",))
        messages.success(request, "وضعیت به «در جریان» تغییر کرد.")
    elif action == "done":
        handoff.status = "done"
        handoff.save(update_fields=("status",))
        messages.success(request, "درخواست به «انجام شد» تغییر کرد.")
    elif action == "delete":
        handoff.delete()
        messages.success(request, "درخواست حذف شد.")
    else:
        messages.error(request, "عملیات نامعتبر.")
    return redirect("panel:handoff")


# ─── Knowledge base (documents + crawler) ─────────────────────────────────

@staff_member_required
def knowledge(request):
    from .forms import KnowledgeUploadForm

    upload_form = KnowledgeUploadForm()
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "upload":
            upload_form = KnowledgeUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                from .document_pipeline import detect_file_type

                created = 0
                for key in ("file", "file2", "file3"):
                    f = upload_form.cleaned_data.get(key)
                    if not f:
                        continue
                    title = (upload_form.cleaned_data.get("title") or "").strip()
                    # When multiple files, title applies to first only; others use filename.
                    if created > 0:
                        title = ""
                    doc = Document(
                        title=title or f.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:200],
                        file=f,
                        file_type=detect_file_type(f.name) or "",
                        source_type="upload",
                        status="uploaded",
                    )
                    doc.save()
                    # Use the top-level import; do not shadow it locally.
                    doc.status = "queued"
                    doc.save(update_fields=("status", "updated_at"))
                    enqueue_document(doc.pk)
                    created += 1
                if created:
                    messages.success(request, f"{created} سند آپلود شد و در صف پردازش قرار گرفت.")
                return redirect("panel:knowledge")
            messages.error(request, _form_errors(upload_form))

        elif action == "crawl":
            form = CrawlStartForm(request.POST)
            if form.is_valid():
                urls = form.cleaned_data.get("_parsed_urls") or []
                if not urls:
                    messages.error(request, "حداقل یک لینک وارد کنید.")
                elif len(urls) == 1:
                    job = form.save(commit=False)
                    # Multi-URL fields backfill
                    job.source_urls = urls[0]
                    job.crawl_mode = "single"
                    job.max_pages_per_url = form.cleaned_data.get("max_pages") or 30
                    job.save()
                    try:
                        enqueue_crawl_job(job.pk)
                    except Exception as exc:
                        messages.warning(request, f"کار کرال ثبت شد ولی اجرای خودکار ناموفق بود: {exc}")
                    else:
                        messages.success(request, "کرال آغاز شد؛ پیشرفت در همین صفحه دیده می‌شود.")
                else:
                    # Fan-out: one job per URL so each host is crawled independently.
                    started = 0
                    for url in urls[:20]:
                        job = CrawlJob(
                            start_url=url,
                            source_urls="\n".join(urls),
                            crawl_mode="multi",
                            max_pages=form.cleaned_data.get("max_pages") or 30,
                            max_pages_per_url=form.cleaned_data.get("max_pages") or 30,
                        )
                        job.save()
                        try:
                            enqueue_crawl_job(job.pk)
                            started += 1
                        except Exception:
                            pass
                    messages.success(request, f"{started} کار کرال جداگانه برای {len(urls)} لینک آغاز شد.")
                return redirect("panel:knowledge")
            messages.error(request, _form_errors(form))

        elif action == "recrawl" and request.POST.get("job"):
            job = get_object_or_404(CrawlJob, pk=request.POST["job"])
            job.status = "queued"
            job.pages_indexed = 0
            job.pages_failed = 0
            job.save(update_fields=("status", "pages_indexed", "pages_failed", "updated_at"))
            enqueue_crawl_job(job.pk)
            messages.success(request, "کرال دوباره در صف قرار گرفت.")
            return redirect("panel:knowledge")

        elif action == "reprocess" and request.POST.get("document"):
            document = get_object_or_404(Document, pk=request.POST["document"])
            document.status = "queued"
            document.error_message = ""
            document.save(update_fields=("status", "error_message", "updated_at"))
            enqueue_document(document.pk)
            messages.success(request, "سند دوباره در صف پردازش قرار گرفت.")
            return redirect("panel:knowledge")

    documents = Document.objects.all()
    jobs = CrawlJob.objects.all()[:12]
    return render(request, "panel/knowledge.html", {
        "documents": documents,
        "documents_ready": documents.filter(status="ready").count(),
        "documents_failed": documents.filter(status="failed").count(),
        "documents_queued": documents.filter(status__in=("queued", "processing")).count(),
        "jobs": jobs,
        "crawl_form": CrawlStartForm(),
        "upload_form": upload_form,
        "nav": "knowledge",
    })


@staff_member_required
@require_POST
def knowledge_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    from .document_pipeline import delete_document_artifacts

    delete_document_artifacts(document)
    messages.success(request, "سند و قطعات شناختی آن حذف شد.")
    return redirect("panel:knowledge")


# ─── Widget customizer (live preview) ─────────────────────────────────────

@staff_member_required
def customizer(request):
    config = WidgetConfig.objects.first() or WidgetConfig.objects.create()
    if request.method == "POST":
        appearance = WidgetAppearanceForm(request.POST, request.FILES, instance=config)
        behavior = WidgetBehaviorForm(request.POST, instance=config)
        if appearance.is_valid() and behavior.is_valid():
            behavior.save(commit=False)
            appearance.save()
            behavior.instance = config
            behavior.save()
            cache.delete("ai-support:widget-config")
            messages.success(request, "تنظیمات ظاهری ذخیره شد؛ پیش‌نمایش زنده به‌روز است.")
            return redirect("panel:customizer")
        else:
            messages.error(request, _form_errors(appearance) or _form_errors(behavior))
            appearance = WidgetAppearanceForm(instance=config)
            behavior = WidgetBehaviorForm(instance=config)
    else:
        appearance = WidgetAppearanceForm(instance=config)
        behavior = WidgetBehaviorForm(instance=config)

    preview_payload = json.dumps(_preview_config(config), ensure_ascii=False)
    return render(request, "panel/customizer.html", {
        "appearance": appearance,
        "behavior": behavior,
        "preview_payload": preview_payload,
        "widget_theme": config.widget_theme,
        "nav": "customizer",
    })


def _preview_config(config):
    """The live-preview payload mirrors widget_config_payload appearance keys."""
    icon_url = ""
    if config.icon_type == "custom" and config.custom_icon_file:
        try:
            icon_url = config.custom_icon_file.url
        except Exception:
            icon_url = ""
    return {
        "title": config.title,
        "subtitle": config.subtitle,
        "greeting": config.greeting,
        "primaryColor": config.primary_color,
        "secondaryColor": config.secondary_color,
        "accentColor": config.accent_color,
        "headerBadge": config.header_badge,
        "botAvatarText": config.bot_avatar_text,
        "inputPlaceholder": config.input_placeholder,
        "themeMode": config.theme_mode,
        "darkMode": config.dark_mode,
        "bubbleStyle": config.bubble_style,
        "panelWidth": config.panel_width,
        "panelHeight": config.panel_height,
        "borderRadius": config.border_radius,
        "mobileFullscreen": config.mobile_fullscreen,
        "logoUrl": config.logo_url,
        "fontFamily": config.font_family,
        "fontSize": config.font_size,
        "position": config.position,
        "positionVerticalOffset": config.position_vertical_offset,
        "positionHorizontalOffset": config.position_horizontal_offset,
        "iconType": config.icon_type,
        "defaultIconChoice": config.default_icon_choice,
        "customIconUrl": icon_url,
        "showPoweredBy": config.show_powered_by,
        "showTimestamp": config.show_timestamp,
        "showAvatar": config.show_avatar,
        "showFeedback": config.show_feedback,
        "enableSounds": config.enable_sounds,
        "enableAnimations": config.enable_animations,
        "enableConversationMemory": config.enable_conversation_memory,
        "contextWindow": config.context_window,
        "showCitations": config.show_citations,
        "enableLeadCapture": config.enable_lead_capture,
        "enableHandoff": config.enable_handoff,
        "leadFormTitle": config.lead_form_title,
        "leadFormDescription": config.lead_form_description,
        "handoffMessage": config.handoff_message,
        "suggestions": config.suggestions or [],
    }


# ─── Installation ─────────────────────────────────────────────────────────

@staff_member_required
def installation(request):
    provider = ProviderSettings.objects.first()
    if provider is None:
        provider = ProviderSettings.objects.create()
    if request.method == "POST":
        form = InstallationForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            cache.delete("ai-support:installation")
            messages.success(request, "دامنه‌ها و کلید نصب ذخیره شد (تا ۱۰ ثانیه اعمال می‌شود).")
            return redirect("panel:installation")
        messages.error(request, _form_errors(form))
        form = InstallationForm(instance=provider)
    else:
        form = InstallationForm(instance=provider)

    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    base = f"{scheme}://{host}"
    config = WidgetConfig.objects.first()
    theme = (config.widget_theme if config else "classic") or "classic"
    widget_file = "widget.js" if theme == "classic" else f"widget-{theme}.js"
    snippet = (
        f'<script src="{base}/static/widget/{widget_file}"\n'
        f'        data-api="{base}/api/chat/"\n'
        f'        data-widget-key="{provider.widget_public_key}"></script>'
    )
    return render(request, "panel/installation.html", {
        "form": form,
        "snippet": snippet,
        "base_url": base,
        "demo_url": f"{base}/demo/",
        "widget_key": provider.widget_public_key,
        "widget_theme": theme,
        "widget_file": widget_file,
        "allowed_origins": provider.allowed_origins_list,
        "nav": "installation",
    })


@staff_member_required
def installation_key(request):
    """Rotate the public widget key (regenerates a new installation key)."""
    import uuid

    provider = ProviderSettings.objects.first()
    if provider is None:
        provider = ProviderSettings.objects.create()
    provider.widget_public_key = uuid.uuid4().hex
    provider.save(update_fields=("widget_public_key", "updated_at"))
    cache.delete("ai-support:installation")
    messages.success(request, "کلید نصب جدید ساخته شد؛ کد نصب را روی سایت مشتری به‌روز کنید.")
    return redirect("panel:installation")


# ─── Onboarding wizard ────────────────────────────────────────────────────

@staff_member_required
def wizard(request):
    provider = ProviderSettings.objects.first()
    config = WidgetConfig.objects.first() or WidgetConfig.objects.create()
    steps = [
        {
            "n": 1,
            "title": "معرفی سایت",
            "done": bool(provider and provider.widget_public_key),
            "desc": "کلید نصب ساخته شود و دامنه‌ی سایت ثبت شود.",
            "url": reverse("panel:installation"),
        },
        {
            "n": 2,
            "title": "تنظیم هوش مصنوعی",
            "done": bool(provider and (provider.llm_api_key or provider.llm_model)),
            "desc": "کلید LLM و مدل پاسخ‌دهی از تنظیمات AI ثبت شود.",
            "url": reverse("panel:ai-settings"),
        },
        {
            "n": 3,
            "title": "افزودن دانش",
            "done": Document.objects.filter(status="ready").exists(),
            "desc": "حداقل یک سند یا سایت خزیده‌شده آماده باشد.",
            "url": reverse("panel:knowledge"),
        },
        {
            "n": 4,
            "title": "شخصی‌سازی ویجت",
            "done": bool(config.title and config.primary_color),
            "desc": "رنگ، عنوان و پیام خوش‌آمد تنظیم شود.",
            "url": reverse("panel:customizer"),
        },
        {
            "n": 5,
            "title": "نصب ویجت",
            "done": bool(provider and provider.allowed_origins_list),
            "desc": "کد نصب روی سایت مشتری قرار بگیرد.",
            "url": reverse("panel:installation"),
        },
        {
            "n": 6,
            "title": "تست نهایی",
            "done": False,
            "desc": "ویجت را در حالت واقعی امتحان کنید و پاسخ‌دهی را ببینید.",
            "url": None,
        },
    ]
    completed = sum(1 for step in steps if step["done"])
    return render(request, "panel/wizard.html", {
        "steps": steps,
        "completed": completed,
        "demo_url": request.build_absolute_uri("/demo/"),
        "nav": "wizard",
    })


# ─── AI provider settings ─────────────────────────────────────────────────

@staff_member_required
def ai_settings(request):
    from .forms import PromptBuilderForm

    provider = ProviderSettings.objects.first()
    if provider is None:
        provider = ProviderSettings.objects.create()
    config = WidgetConfig.objects.first() or WidgetConfig.objects.create()

    if request.method == "POST":
        section = request.POST.get("section", "provider")
        if section == "prompt":
            prompt_form = PromptBuilderForm(request.POST, instance=config)
            provider_form = AIProviderForm(instance=provider)
            if prompt_form.is_valid():
                prompt_form.save()
                cache.delete("ai-support:widget-config")
                messages.success(request, "پرامپت ذخیره شد — پاسخ‌های بعدی با همین لحن و هویت تولید می‌شوند.")
                return redirect("panel:ai-settings")
            messages.error(request, _form_errors(prompt_form))
        else:
            provider_form = AIProviderForm(request.POST, instance=provider)
            prompt_form = PromptBuilderForm(instance=config)
            if provider_form.is_valid():
                provider_form.save()
                messages.success(request, "تنظیمات هوش مصنوعی ذخیره شد و بلافاصله اعمال می‌شود.")
                return redirect("panel:ai-settings")
            messages.error(request, _form_errors(provider_form))
    else:
        provider_form = AIProviderForm(instance=provider)
        prompt_form = PromptBuilderForm(instance=config)

    # Live preview of the auto-generated prompt
    try:
        from .models import build_auto_system_prompt
        auto_preview = build_auto_system_prompt(config)
    except Exception:
        auto_preview = ""

    return render(request, "panel/ai_settings.html", {
        "form": provider_form,
        "prompt_form": prompt_form,
        "auto_preview": auto_preview,
        "config": config,
        "nav": "ai-settings",
    })


@staff_member_required
def business_rules(request):
    from .forms import BusinessRuleForm
    from .models import BusinessRule
    from .models import INTENT_CHOICES

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "delete":
            rule = get_object_or_404(BusinessRule, pk=request.POST.get("rule_id"))
            rule.delete()
            from .business_rules import invalidate_rules_cache
            invalidate_rules_cache()
            messages.success(request, "قانون حذف شد.")
            return redirect("panel:business-rules")
        if action == "toggle":
            rule = get_object_or_404(BusinessRule, pk=request.POST.get("rule_id"))
            rule.enabled = not rule.enabled
            rule.save(update_fields=("enabled", "updated_at"))
            from .business_rules import invalidate_rules_cache
            invalidate_rules_cache()
            messages.success(request, "وضعیت قانون تغییر کرد.")
            return redirect("panel:business-rules")

        form = BusinessRuleForm(request.POST)
        if form.is_valid():
            form.save()
            from .business_rules import invalidate_rules_cache
            invalidate_rules_cache()
            messages.success(request, "قانون جدید ذخیره شد.")
            return redirect("panel:business-rules")
        messages.error(request, _form_errors(form))
        form = BusinessRuleForm(request.POST)
    else:
        form = BusinessRuleForm()

    from .models import BusinessRule
    rules = BusinessRule.objects.all().order_by("priority", "-updated_at")
    # Provide intent choices to the template for the trigger dropdown helper
    return render(request, "panel/business_rules.html", {
        "form": form,
        "rules": rules,
        "intent_choices": INTENT_CHOICES,
        "nav": "business-rules",
    })


# ─── Widget preview page (customizer iframe) ──────────────────────────────

@staff_member_required
def preview(request):
    return render(request, "panel/preview.html")


# ─── Health API for the dashboard pulse strip ─────────────────────────────

@staff_member_required
def health_summary(request):
    from django.db import connection

    provider = ProviderSettings.objects.first()
    config = WidgetConfig.objects.first()
    # Corpus is healthy when all three artifacts exist, or none do (fresh install).
    from .document_pipeline import CHUNKS_PATH, METADATA_PATH, EMBEDDINGS_PATH

    existing = sum(1 for p in (CHUNKS_PATH, METADATA_PATH, EMBEDDINGS_PATH) if p.exists())
    corpus_ok = existing in (0, 3)
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_ok = False
    return JsonResponse({
        "database": db_ok,
        "corpus": corpus_ok,
        "llm_key": bool(provider and provider.llm_api_key),
        "widget_key": bool(provider and provider.widget_public_key),
        "origins": len(provider.allowed_origins_list) if provider else 0,
        "streaming": bool(config and config.enable_streaming),
    })
