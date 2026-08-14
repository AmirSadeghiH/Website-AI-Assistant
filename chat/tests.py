from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AnalyticsEvent, Conversation, Message, WidgetConfig


class ChatEndpointTests(TestCase):
    def setUp(self):
        self.config = WidgetConfig.objects.create(
            business_name="Demo business",
            title="دستیار آزمایشی",
            faq_url="https://example.com/faq/",
            privacy_url="https://example.com/privacy/",
            suggestions=["شرایط دریافت وام؟", "تماس با پشتیبانی"],
        )

    @patch("chat.views.get_rag_service")
    def test_chat_returns_rag_answer_and_persists_messages(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ آزمایشی"

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
            HTTP_ORIGIN="https://merchant.example",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["answer"], "پاسخ آزمایشی")
        self.assertIsNotNone(payload["conversation_id"])
        self.assertIsNotNone(payload["message_id"])
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.filter(role="user").count(), 1)
        self.assertEqual(Message.objects.filter(role="assistant").count(), 1)
        get_rag_service.return_value.ask.assert_called_once()
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "*",
        )

    def test_chat_rejects_invalid_payloads(self):
        cases = (
            (b"not-json", "invalid_json", 400),
            (b"[]", "invalid_payload", 400),
            (b'{"message": 123}', "invalid_message", 400),
            (b'{"message": "   "}', "message_required", 400),
            ('{"message": "سلام", "history": {}}'.encode(), "invalid_history", 400),
        )

        for body, error_code, status_code in cases:
            with self.subTest(error_code=error_code):
                response = self.client.post(
                    "/api/chat/",
                    data=body,
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, status_code)
                self.assertEqual(response.json()["error"], error_code)

    def test_chat_rejects_messages_over_limit(self):
        response = self.client.post(
            "/api/chat/",
            data={"message": "x" * 4001},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"], "message_too_long")

    def test_health_endpoint(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["mode"], "single-site")

    @patch("chat.views.get_rag_service")
    def test_widget_config_history_and_feedback(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ آزمایشی"

        config_response = self.client.get("/api/widget-config/")
        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(config_response.json()["business_name"], "Demo business")
        self.assertEqual(config_response.json()["suggestions"], self.config.suggestions)

        chat_response = self.client.post(
            "/api/chat/",
            data={"conversation_id": "conv-test", "message": "سلام"},
            content_type="application/json",
        )
        self.assertEqual(chat_response.status_code, 200)
        payload = chat_response.json()

        history_response = self.client.get(
            "/api/history/?conversation_id=conv-test",
        )
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.json()["messages"]), 2)

        feedback_response = self.client.post(
            "/api/feedback/",
            data={
                "conversation_id": "conv-test",
                "message_id": payload["message_id"],
                "feedback": "helpful",
            },
            content_type="application/json",
        )
        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(
            Message.objects.get(pk=payload["message_id"]).feedback,
            "helpful",
        )
        self.assertTrue(
            AnalyticsEvent.objects.filter(event_type="answer_helpful").exists(),
        )

    def test_events_create_conversation_for_widget_lifecycle(self):
        response = self.client.post(
            "/api/events/",
            data={
                "conversation_id": "event-conv",
                "event_type": "widget_loaded",
                "metadata": {"version": "beta"},
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AnalyticsEvent.objects.filter(
                event_type="widget_loaded",
                conversation__external_id="event-conv",
            ).exists(),
        )

    def test_widget_config_is_singleton(self):
        response = self.client.get("/api/widget-config/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WidgetConfig.objects.count(), 1)


class SupportAdminTests(TestCase):
    def test_custom_admin_dashboard_renders(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="safe-password-123",
        )
        self.client.force_login(user)

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Support")
        self.assertContains(response, "Control Room")
        self.assertContains(response, "Widget settings")
