"""Smoke test: every /panel/ page must render 200 for staff, redirect for anon."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

from django.contrib.auth.models import User
from django.test import Client

from chat.models import (
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

# Seed minimal data (idempotent: clean leftovers from previous runs first)
user, _ = User.objects.get_or_create(username="panel_smoke", is_staff=True)
user.set_password("x-pass-123")
user.save()

# leftover cleanup
Feedback.objects.filter(message__conversation__messages__content="سلام قیمت چنده؟").delete()
Conversation.objects.filter(messages__content="سلام قیمت چنده؟").delete()
Conversation.objects.filter(origin="panel_smoke").delete()
UnansweredQuestion.objects.filter(question="ساعات کاری جمعه چیه؟").delete()
Document.objects.filter(title="سند تست").delete()
CrawlJob.objects.filter(start_url="https://example.com").delete()
Lead.objects.filter(email="t@ex.com").delete()

provider = ProviderSettings.objects.first() or ProviderSettings.objects.create()
config = WidgetConfig.objects.first() or WidgetConfig.objects.create()

conv = Conversation.objects.create(status="open", origin="panel_smoke")
Message.objects.create(conversation=conv, role="user", content="سلام قیمت چنده؟", intent="pricing")
Message.objects.create(
    conversation=conv, role="assistant", content="قیمت‌ها در صفحه محصولات هست.",
    intent="pricing", latency_ms=420, sources=[{"title": "قیمت‌ها", "url": "https://ex.com/p"}],
)
Feedback.objects.create(message=Message.objects.filter(role="assistant").first(), helpful=True)
Lead.objects.create(name="مشتری تست", email="t@ex.com", source="widget_form", conversation=conv)
HandoffRequest.objects.create(conversation=conv, channel="telegram", question="با کارشناس صحبت کنم", status="new")
UnansweredQuestion.objects.create(question="ساعات کاری جمعه چیه؟", reason="no_context", count=3)
Document.objects.create(title="سند تست", source_text="متن آزمایشی", status="ready", source_type="upload")
CrawlJob.objects.create(start_url="https://example.com", max_pages=5, status="done", pages_indexed=3)

client = Client()
paths = [
    "/panel/",
    "/panel/conversations/",
    f"/panel/conversations/{conv.pk}/",
    "/panel/unanswered/",
    "/panel/leads/",
    "/panel/handoff/",
    "/panel/knowledge/",
    "/panel/customizer/",
    "/panel/preview/",
    "/panel/installation/",
    "/panel/wizard/",
    "/panel/ai-settings/",
    "/panel/health-summary/",
]

# Anonymous must be redirected to admin login
anon = Client()

for path in paths:
    resp = anon.get(path)
    assert resp.status_code == 302, f"anon {path} -> {resp.status_code}"
print("ANON redirects OK")

# Staff must render OK
client = Client()
client.force_login(user)
ok = True
for path in paths:
    resp = client.get(path)
    status = resp.status_code
    print(f"{status} {path}")
    if status != 200:
        ok = False
        try:
            print(resp.content.decode("utf-8")[:2000])
        except Exception:
            pass

# Anonymous API endpoints must NOT get panel pages (security spot-check)
resp = anon.get("/panel/health-summary/")
assert resp.status_code == 302, "health-summary must require staff"

# Cleanup smoke data
Conversation.objects.filter(origin="panel_smoke").delete()
UnansweredQuestion.objects.filter(question="ساعات کاری جمعه چیه؟").delete()
Document.objects.filter(title="سند تست").delete()
CrawlJob.objects.filter(start_url="https://example.com").delete()

if ok:
    print("PANEL SMOKE: ALL PAGES OK")
    sys.exit(0)
sys.exit(1)
