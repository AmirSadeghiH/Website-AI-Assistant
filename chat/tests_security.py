"""Security & contract tests for the v2/v3 product endpoints.

Covers:
- /api/history/  — HMAC conversation-token ownership (WP6 #16)
- /api/feedback/ — per-message feedback bound to conversation token
- /api/leads/    — honeypot, validation, throttling (#11)
- /api/handoff/  — channel validation, conversation hand-off (#12)
- /api/chat/stream/ — SSE event contract (#2)
- Crawler SSRF guard (WP5)
- Intent detection (#7)
- Panel auth baseline (WP7)
"""

import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from .conversation_tokens import make_conversation_token
from .crawler import CrawlBlockedError, resolve_public_host
from .intents import detect_intent, normalize_question_key
from .models import (
    Conversation,
    Feedback,
    HandoffRequest,
    Lead,
    Message,
    ProviderSettings,
    UnansweredQuestion,
    WidgetConfig,
)


def _stream_events(response):
    """Parse a StreamingHttpResponse SSE body into [(event, payload), ...]."""
    raw = b"".join(response.streaming_content).decode("utf-8")
    events = []
    for chunk in raw.split("\n\n"):
        if not chunk.strip():
            continue
        name = "message"
        lines = []
        for line in chunk.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                lines.append(line[5:].strip())
        payload = json.loads("\n".join(lines)) if lines else {}
        events.append((name, payload))
    return events


class HistoryEndpointTests(TestCase):
    """HMAC-protected conversation history."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")

    def _create_conversation(self):
        conversation = Conversation.objects.create()
        Message.objects.create(
            conversation=conversation, role="user", content="سلام"
        )
        Message.objects.create(
            conversation=conversation, role="assistant", content="درود!"
        )
        return conversation

    def test_history_requires_valid_token(self):
        conversation = self._create_conversation()
        url = f"/api/history/?conversation_id={conversation.conversation_id}"

        response = self.client.get(url + "&token=bogus-token")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "invalid_token")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            url, HTTP_X_CONVERSATION_TOKEN="wrong-token-123456"
        )
        self.assertEqual(response.status_code, 403)

    def test_history_returns_messages_with_valid_token(self):
        conversation = self._create_conversation()
        token = make_conversation_token(conversation.conversation_id)
        response = self.client.get(
            f"/api/history/?conversation_id={conversation.conversation_id}",
            HTTP_X_CONVERSATION_TOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["messages"]), 2)
        roles = [m["role"] for m in payload["messages"]]
        self.assertEqual(roles, ["user", "assistant"])

    def test_history_unknown_conversation_returns_empty(self):
        token = make_conversation_token("nonexistent-conversation-id-123")
        response = self.client.get(
            "/api/history/?conversation_id=nonexistent-conversation-id-123",
            HTTP_X_CONVERSATION_TOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["messages"], [])


class PerMessageFeedbackTests(TestCase):
    """Feedback bound to a specific message id + conversation token."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")
        self.conversation = Conversation.objects.create()
        self.assistant_message = Message.objects.create(
            conversation=self.conversation,
            role="assistant",
            content="پاسخ",
        )
        self.token = make_conversation_token(self.conversation.conversation_id)

    def _payload(self, **overrides):
        base = {
            "helpful": True,
            "message_id": self.assistant_message.pk,
            "conversation_id": self.conversation.conversation_id,
            "conversation_token": self.token,
        }
        base.update(overrides)
        return base

    def test_feedback_saves_per_message_row(self):
        response = self.client.post(
            "/api/feedback/", data=self._payload(), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["feedback_saved"])
        row = Feedback.objects.filter(message=self.assistant_message).first()
        self.assertIsNotNone(row)
        self.assertTrue(row.helpful)

    def test_feedback_rejects_wrong_conversation_token(self):
        response = self.client.post(
            "/api/feedback/",
            data=self._payload(conversation_token="forged-token"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Feedback.objects.filter(message=self.assistant_message).exists()
        )

    def test_feedback_upsert_same_message(self):
        self.client.post(
            "/api/feedback/", data=self._payload(), content_type="application/json"
        )
        self.client.post(
            "/api/feedback/",
            data=self._payload(helpful=False),
            content_type="application/json",
        )
        rows = Feedback.objects.filter(message=self.assistant_message)
        self.assertEqual(rows.count(), 1)
        self.assertFalse(rows.first().helpful)

    def test_feedback_message_id_without_matching_conversation_ignored(self):
        """A forged message_id + no valid token must not persist a row."""
        response = self.client.post(
            "/api/feedback/",
            data=self._payload(conversation_token=""),
            content_type="application/json",
        )
        # Feedback is best-effort: without token the per-message save is
        # skipped (403) — no forged ownership.
        self.assertEqual(response.status_code, 403)


class LeadEndpointTests(TestCase):
    """Lead capture: honeypot, validation, throttle."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")

    def _valid_payload(self, **overrides):
        base = {
            "name": "مشتری نمونه",
            "email": "customer@example.com",
            "phone": "",
            "note": "درخواست پیش‌فاکتور",
        }
        base.update(overrides)
        return base

    def test_lead_created_with_email_only(self):
        response = self.client.post(
            "/api/leads/", data=self._valid_payload(), content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.source, "widget_form")

    def test_lead_created_with_phone_only(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(email="", phone="09121234567"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.first()
        self.assertEqual(lead.phone, "09121234567")

    def test_lead_requires_contact_channel(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(email="", phone=""),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    def test_lead_rejects_short_name(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(name="م"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_lead_rejects_bad_phone(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(email="", phone="call me maybe"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_honeypot_returns_fake_success_and_stores_nothing(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(website="http://spam.example"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Lead.objects.count(), 0)

    def test_lead_binds_conversation_with_valid_token(self):
        conversation = Conversation.objects.create()
        token = make_conversation_token(conversation.conversation_id)
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(
                conversation_id=conversation.conversation_id,
                conversation_token=token,
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        lead = Lead.objects.first()
        self.assertEqual(lead.conversation_id, conversation.pk)

    def test_lead_ignores_conversation_with_invalid_token(self):
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(
                conversation_id="abc123",
                conversation_token="forged",
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Lead.objects.first().conversation)

    def test_lead_rate_limited(self):
        from django.conf import settings as dj_settings

        rates = dj_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        limit = int(rates["widget_leads"].split("/")[0])
        for index in range(limit):
            response = self.client.post(
                "/api/leads/",
                data=self._valid_payload(email=f"user{index}@example.com"),
                content_type="application/json",
            )
            self.assertIn(response.status_code, (201, 200))
        response = self.client.post(
            "/api/leads/",
            data=self._valid_payload(email="overflow@example.com"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 429)


class HandoffEndpointTests(TestCase):
    """Human handoff: channels + conversation status."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")

    def test_handoff_requires_known_channel(self):
        response = self.client.post(
            "/api/handoff/",
            data={"channel": "sms", "message": "سلام"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_handoff_creates_request_and_marks_conversation(self):
        conversation = Conversation.objects.create()
        token = make_conversation_token(conversation.conversation_id)
        response = self.client.post(
            "/api/handoff/",
            data={
                "channel": "telegram",
                "message": "می‌خوام با اپراتور حرف بزنم",
                "conversation_id": conversation.conversation_id,
                "conversation_token": token,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(HandoffRequest.objects.filter(channel="telegram").exists())
        conversation.refresh_from_db()
        self.assertEqual(conversation.status, "handed_off")

    def test_handoff_without_conversation_still_accepted(self):
        response = self.client.post(
            "/api/handoff/",
            data={"channel": "email", "message": "راهنمایی لازم دارم"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        row = HandoffRequest.objects.first()
        self.assertIsNone(row.conversation)

    def test_handoff_rejects_empty_message(self):
        response = self.client.post(
            "/api/handoff/",
            data={"channel": "email", "message": "   "},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class ChatStreamContractTests(TestCase):
    """SSE stream: meta → token… → done event sequence."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")

    @patch("chat.views.get_rag_service")
    def test_stream_emits_meta_tokens_done(self, get_rag_service):
        def fake_stream(question, history=None):
            yield {"type": "token", "text": "سلام"}
            yield {"type": "token", "text": " خوبید؟"}
            yield {
                "type": "done",
                "result": {
                    "answer": "سلام خوبید؟",
                    "sources": [{"title": "مستند", "url": "https://x.example/a"}],
                    "used_fallback": False,
                    "reason": None,
                    "confidence": 0.9,
                },
                "cached": False,
            }

        service = get_rag_service.return_value
        service.stream_answer.side_effect = fake_stream

        response = self.client.post(
            "/api/chat/stream/",
            data={"message": "سلام"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-store")

        events = _stream_events(response)
        names = [name for name, _ in events]
        self.assertEqual(names[0], "meta")
        self.assertEqual(names[-1], "done")
        self.assertIn("token", names)

        meta = events[0][1]
        self.assertIn("conversation_id", meta)
        self.assertIn("conversation_token", meta)
        self.assertIn("intent", meta)

        done = events[-1][1]
        self.assertIn("message_id", done)
        self.assertEqual(done["citations"][0]["title"], "مستند")
        self.assertFalse(done["fallback"])
        # Assistant message persisted
        self.assertTrue(
            Message.objects.filter(role="assistant", content="سلام خوبید؟").exists()
        )

    @patch("chat.views.get_rag_service")
    def test_stream_marks_fallback_and_records_unanswered(self, get_rag_service):
        def fake_stream(question, history=None):
            yield {"type": "token", "text": "..."}
            yield {
                "type": "done",
                "result": {
                    "answer": "متأسفم، اطلاعات دقیقی در دانش فعلی من برای پاسخ به این سؤال وجود ندارد.",
                    "sources": [],
                    "used_fallback": True,
                    "reason": "no_context",
                    "confidence": 0.1,
                },
                "cached": False,
            }

        get_rag_service.return_value.stream_answer.side_effect = fake_stream

        response = self.client.post(
            "/api/chat/stream/",
            data={"message": "سؤال خیلی عجیب نامربوط"},
            content_type="application/json",
        )
        events = _stream_events(response)
        done = events[-1][1]
        self.assertTrue(done["fallback"])
        self.assertTrue(
            UnansweredQuestion.objects.filter(
                reason="no_context"
            ).exists()
        )

    def test_stream_rejects_invalid_payload(self):
        response = self.client.post(
            "/api/chat/stream/",
            data={"message": "   "},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("chat.views.get_rag_service")
    def test_stream_binds_conversation_id(self, get_rag_service):
        get_rag_service.return_value.stream_answer.return_value = iter(
            [
                {
                    "type": "done",
                    "result": {
                        "answer": "پاسخ",
                        "sources": [],
                        "used_fallback": False,
                        "reason": None,
                        "confidence": 0.8,
                    },
                    "cached": False,
                }
            ]
        )
        existing = Conversation.objects.create()
        response = self.client.post(
            "/api/chat/stream/",
            data={"message": "سلام", "conversation_id": existing.conversation_id},
            content_type="application/json",
        )
        events = _stream_events(response)
        meta = events[0][1]
        self.assertEqual(meta["conversation_id"], existing.conversation_id)
        existing.refresh_from_db()
        self.assertEqual(existing.message_count, 2)


class CrawlerSSRFTests(TestCase):
    """SSRF guard must reject non-public targets with CrawlBlockedError."""

    def test_rejects_localhost(self):
        for url in ("http://127.0.0.1/x", "http://localhost:8000/"):
            with self.subTest(url=url):
                with self.assertRaises(CrawlBlockedError):
                    resolve_public_host(url)

    def test_rejects_private_ranges(self):
        for url in (
            "http://10.0.0.5/",
            "http://192.168.1.10/",
            "http://172.16.0.1/",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://[fd00::1]/",
        ):
            with self.subTest(url=url):
                with self.assertRaises(CrawlBlockedError):
                    resolve_public_host(url)

    def test_rejects_non_http_schemes(self):
        for url in ("file:///etc/passwd", "ftp://example.com/"):
            with self.subTest(url=url):
                with self.assertRaises(CrawlBlockedError):
                    resolve_public_host(url)

    def test_rejects_userinfo_and_bogus(self):
        for url in ("http://user:pass@example.com/", "not a url"):
            with self.subTest(url=url):
                with self.assertRaises(CrawlBlockedError):
                    resolve_public_host(url)

    def test_accepts_public_target_without_dns(self):
        """Public literal IPs pass without DNS resolution surprises."""
        from unittest.mock import patch as _patch

        infos = [(2, 1, 6, "", ("93.184.216.34", 0))]
        with _patch("chat.crawler.socket.getaddrinfo", return_value=infos):
            hostname = resolve_public_host("http://93.184.216.34/page")
        self.assertEqual(hostname, "93.184.216.34")


class IntentDetectionTests(TestCase):
    """Rule-based intent detection (#7)."""

    def test_contact_request(self):
        self.assertEqual(detect_intent("شماره تماس پشتیبانی چنده؟"), "contact_request")

    def test_pricing(self):
        self.assertEqual(detect_intent("قیمت چقدره؟"), "pricing")

    def test_greeting(self):
        self.assertEqual(detect_intent("سلام"), "greeting")

    def test_general_fallback(self):
        self.assertEqual(detect_intent("هوا امروز خوبه"), "general")

    def test_arabic_normalization(self):
        self.assertEqual(detect_intent("﷼ قیمتش چند؟"), "pricing")

    def test_normalize_question_key_stable(self):
        self.assertEqual(
            normalize_question_key("سؤال  اول!"),
            normalize_question_key("سوال   اول؟"),
        )


class PanelAuthTests(TestCase):
    """Custom admin panel requires staff and redirects anonymous users."""

    PANEL_PATHS = (
        "/panel/",
        "/panel/conversations/",
        "/panel/unanswered/",
        "/panel/leads/",
        "/panel/handoff/",
        "/panel/knowledge/",
        "/panel/customizer/",
        "/panel/installation/",
        "/panel/wizard/",
        "/panel/ai-settings/",
        "/panel/health-summary/",
    )

    def test_anonymous_redirected(self):
        for path in self.PANEL_PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("admin/login", response.url)

    def test_staff_sees_dashboard(self):
        from django.contrib.auth.models import User

        User.objects.create_user("staffer", password="pw12345!", is_staff=True)
        self.assertTrue(self.client.login(username="staffer", password="pw12345!"))
        response = self.client.get("/panel/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/panel/health-summary/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ("database", "corpus", "llm_key", "widget_key"):
            self.assertIn(key, payload)
