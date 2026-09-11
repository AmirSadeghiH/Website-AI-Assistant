"""Plan metering tests — quotas, units, cycles, expiry enforcement.

Covers:
- compute_units (input-size presets → message units)
- add_months / get_monthly_window calendar arithmetic
- quota_info usage aggregation
- Manual chat-close (quota_locked): /api/chat/ 403 + stream done + history flag
- WidgetConfig.input_size_class drives unit computation on user messages
- plan_activate (command room): renew extends, expired re-activates with
  fresh key + restored origins
- Expiry enforcement: key rotation + origins stash + staff lock screen
- WidgetAccessPermission rejects when expired
"""

import json
from datetime import timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from .plans import (
    PLAN_LIMITS,
    add_months,
    compute_units,
    get_monthly_window,
    quota_info,
)
from .models import (
    Conversation,
    Message,
    ProviderSettings,
    SiteProfile,
    WidgetConfig,
)

User = get_user_model()


def _stream_events(response):
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


class ComputeUnitsTests(TestCase):
    def test_short_question_is_one_unit(self):
        # The product-team example: ~40 chars → 1 unit at every preset
        q = "محتویات داخل جعبه ی محصول x چیا هستش؟"
        for size in ("very_low", "low", "medium", "high", "very_high"):
            self.assertEqual(compute_units(q, size), 1, size)

    def test_long_message_scales(self):
        long_msg = "x" * 1800
        self.assertEqual(compute_units(long_msg, "very_low"), 12)   # 1800/150
        self.assertEqual(compute_units(long_msg, "medium"), 3)      # 1800/600
        self.assertEqual(compute_units(long_msg, "very_high"), 1)   # 1800/2400

    def test_edge_lengths(self):
        self.assertEqual(compute_units("", "medium"), 1)            # empty = 1
        self.assertEqual(compute_units("a" * 601, "medium"), 2)     # just over
        self.assertEqual(compute_units("a" * 600, "medium"), 1)     # exactly


class CalendarMathTests(TestCase):
    def test_add_months_clamps_day(self):
        dt = timezone.datetime(2026, 1, 31, 12, 0, tzinfo=dt_timezone.utc)
        res = add_months(dt, 1)
        self.assertEqual((res.year, res.month, res.day), (2026, 2, 28))

    def test_add_months_year_rollover(self):
        dt = timezone.datetime(2026, 11, 15, tzinfo=dt_timezone.utc)
        res = add_months(dt, 3)
        self.assertEqual((res.year, res.month, res.day), (2027, 2, 15))

    def test_monthly_window_from_activation(self):
        # Anchor Jan 15; on Feb 20 the window is Feb 15 → Mar 15
        anchor = timezone.datetime(2026, 1, 15, 10, 0, tzinfo=dt_timezone.utc)
        now = timezone.datetime(2026, 2, 20, tzinfo=dt_timezone.utc)
        cs, ce = get_monthly_window(anchor, now)
        self.assertEqual((cs.year, cs.month, cs.day), (2026, 2, 15))
        self.assertEqual((ce.year, ce.month, ce.day), (2026, 3, 15))

    def test_monthly_window_before_activation(self):
        anchor = timezone.now() + timedelta(days=5)
        cs, ce = get_monthly_window(anchor)
        self.assertEqual(cs, anchor)


class QuotaInfoTests(TestCase):
    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="T")

    def test_usage_sums_user_units_only(self):
        anchor = timezone.now() - timedelta(days=3)
        conv = Conversation.objects.create()
        Message.objects.create(conversation=conv, role="user", content="a", units=2)
        Message.objects.create(conversation=conv, role="user", content="b", units=3)
        Message.objects.create(conversation=conv, role="assistant", content="c", units=99)
        info = quota_info("simple", anchor)
        self.assertEqual(info["used"], 5)
        self.assertEqual(info["limit"], PLAN_LIMITS["simple"])
        self.assertFalse(info["exceeded"])

    def test_exceeded_flag(self):
        anchor = timezone.now() - timedelta(days=1)
        conv = Conversation.objects.create()
        Message.objects.create(conversation=conv, role="user", content="a", units=PLAN_LIMITS["simple"])
        info = quota_info("simple", anchor)
        self.assertTrue(info["exceeded"])

    def test_old_messages_out_of_window(self):
        anchor = timezone.now() - timedelta(days=3)
        conv = Conversation.objects.create()
        old = Message.objects.create(conversation=conv, role="user", content="old", units=7)
        Message.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=40))
        info = quota_info("simple", anchor)
        self.assertEqual(info["used"], 0)


class QuotaLockTests(TestCase):
    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="T", enable_streaming=True)
        ProviderSettings.objects.create(widget_public_key="k" * 32)
        self.sp = SiteProfile.objects.create(quota_locked=True)

    def tearDown(self):
        cache.clear()

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_chat_returns_403_quota_locked(self):
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "سلام"}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="k" * 32,
        )
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(resp.json()["quota_locked"])

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_stream_done_carries_quota_flag(self):
        resp = self.client.post(
            "/api/chat/stream/",
            data=json.dumps({"message": "سلام"}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="k" * 32,
        )
        events = _stream_events(resp)
        done = [p for n, p in events if n == "done"]
        self.assertTrue(done and done[0].get("quota_locked"))

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_history_flag_and_unlock(self):
        conv = Conversation.objects.create()
        Message.objects.create(conversation=conv, role="user", content="سلام")
        from .conversation_tokens import make_conversation_token
        token = make_conversation_token(conv.conversation_id)
        url = f"/api/history/?conversation_id={conv.conversation_id}&token={token}"
        r1 = self.client.get(url, HTTP_X_WIDGET_KEY="k" * 32)
        self.assertTrue(r1.json()["quota_locked"])
        self.sp.quota_locked = False
        self.sp.save(update_fields=["quota_locked", "updated_at"])
        r2 = self.client.get(url, HTTP_X_WIDGET_KEY="k" * 32)
        self.assertFalse(r2.json()["quota_locked"])

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_units_use_input_size_class(self):
        self.sp.quota_locked = False
        self.sp.save(update_fields=["quota_locked", "updated_at"])
        cfg = WidgetConfig.objects.first()
        cfg.input_size_class = "medium"  # 600 chars/unit
        cfg.save(update_fields=["input_size_class", "updated_at"])
        self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "x" * 1300}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="k" * 32,
        )
        msg = Message.objects.filter(role="user").order_by("-pk").first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.units, 3)  # ceil(1300/600)


class PlanActivateTests(TestCase):
    def setUp(self):
        cache.clear()
        self.superuser = User.objects.create_user(
            username="owner", password="pass-123456", is_staff=True, is_superuser=True
        )
        self.provider = ProviderSettings.objects.create(
            widget_public_key="oldkey", widget_allowed_origins="https://shop.example.com\nhttps://a.test"
        )
        self.sp = SiteProfile.objects.create(plan="simple")
        self.client.force_login(self.superuser)

    def tearDown(self):
        cache.clear()

    def test_activate_new_plan(self):
        r = self.client.post("/panel/command-room/plan/activate/", {"plan": "plus", "months": 3})
        self.assertEqual(r.status_code, 302)
        self.sp.refresh_from_db()
        self.assertEqual(self.sp.plan, "plus")
        self.assertEqual(self.sp.period_months, 3)
        self.assertIsNotNone(self.sp.expires_at)
        self.assertFalse(self.sp.suspended)

    def test_renew_extends_from_expiry(self):
        self.client.post("/panel/command-room/plan/activate/", {"plan": "simple", "months": 1})
        self.sp.refresh_from_db()
        first_expiry = self.sp.expires_at
        self.client.post("/panel/command-room/plan/activate/", {"plan": "simple", "months": 3})
        self.sp.refresh_from_db()
        expected = add_months(first_expiry, 3)
        self.assertEqual(self.sp.expires_at.replace(microsecond=0), expected.replace(microsecond=0))

    def test_reactivation_after_expiry_restores_origins_and_rotates_key(self):
        # Simulate an expired, already-enforced state
        self.sp.expires_at = timezone.now() - timedelta(days=1)
        self.sp.suspended = True
        self.sp.suspended_origins = self.provider.widget_allowed_origins
        self.sp.save(update_fields=["expires_at", "suspended", "suspended_origins", "updated_at"])
        self.provider.widget_allowed_origins = ""
        self.provider.widget_public_key = "deadkey"
        self.provider.save(update_fields=["widget_public_key", "widget_allowed_origins", "updated_at"])

        r = self.client.post("/panel/command-room/plan/activate/", {"plan": "pro", "months": 12})
        self.assertEqual(r.status_code, 302)
        self.sp.refresh_from_db()
        self.provider.refresh_from_db()
        self.assertEqual(self.sp.plan, "pro")
        self.assertFalse(self.sp.suspended)
        self.assertEqual(self.provider.widget_allowed_origins, "https://shop.example.com\nhttps://a.test")
        self.assertNotEqual(self.provider.widget_public_key, "deadkey")
        self.assertTrue(self.sp.is_active)


class ExpiryEnforcementTests(TestCase):
    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="T")
        self.provider = ProviderSettings.objects.create(
            widget_public_key="livekey", widget_allowed_origins="https://shop.example.com"
        )
        self.staff = User.objects.create_user(
            username="custadmin", password="pass-123456", is_staff=True, is_superuser=False
        )
        self.superuser = User.objects.create_user(
            username="owner", password="pass-123456", is_staff=True, is_superuser=True
        )
        self.sp = SiteProfile.objects.create(
            plan="simple", period_start=timezone.now() - timedelta(days=40)
        )

    def tearDown(self):
        cache.clear()

    def _expire(self):
        self.sp.expires_at = timezone.now() - timedelta(days=1)
        self.sp.save(update_fields=["expires_at", "updated_at"])
        cache.delete("plan:expired-flag")

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_widget_api_rejects_when_expired(self):
        self._expire()
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "سلام"}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="livekey",
        )
        self.assertEqual(resp.status_code, 403)

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_enforcement_rotates_key_and_clears_origins(self):
        self._expire()
        # Trigger via widget API
        self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "سلام"}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="livekey",
        )
        self.sp.refresh_from_db()
        self.provider.refresh_from_db()
        self.assertTrue(self.sp.suspended)
        self.assertEqual(self.provider.widget_allowed_origins, "")
        self.assertNotEqual(self.provider.widget_public_key, "livekey")
        self.assertEqual(self.sp.suspended_origins, "https://shop.example.com")

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_staff_lock_screen_when_expired(self):
        self._expire()
        self.client.force_login(self.staff)
        resp = self.client.get("/panel/")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("منقضی", resp.content.decode("utf-8"))

    @override_settings(ALLOWED_HOSTS=["testserver"])
    def test_superuser_bypasses_lock(self):
        self._expire()
        self.client.force_login(self.superuser)
        resp = self.client.get("/panel/command-room/")
        self.assertEqual(resp.status_code, 200)

    @override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False)
    def test_widget_works_when_active(self):
        self.sp.expires_at = timezone.now() + timedelta(days=10)
        self.sp.save(update_fields=["expires_at", "updated_at"])
        cache.delete("plan:expired-flag")
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "سلام"}),
            content_type="application/json",
            HTTP_X_WIDGET_KEY="livekey",
        )
        self.assertEqual(resp.status_code, 200)
