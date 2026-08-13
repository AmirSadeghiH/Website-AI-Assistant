from unittest.mock import patch

from django.test import TestCase

from .models import Site, WidgetConfig


class ChatEndpointTests(TestCase):
    def setUp(self):
        site = Site.objects.create(
            name="Demo site",
            slug="demo",
            domain="localhost",
        )
        WidgetConfig.objects.create(site=site)

    @patch("chat.views.get_rag_service")
    def test_chat_returns_rag_answer(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ آزمایشی"

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
            HTTP_ORIGIN="https://merchant.example",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "پاسخ آزمایشی")
        self.assertIsNotNone(response.json()["conversation_id"])
        self.assertIsNotNone(response.json()["message_id"])
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

    @patch("chat.views.get_rag_service")
    def test_widget_config_history_and_feedback(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ آزمایشی"
        config_response = self.client.get("/api/widget-config/?site_id=demo")
        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(config_response.json()["site_id"], "demo")

        conversation_response = self.client.post(
            "/api/chat/",
            data={"site_id": "demo", "conversation_id": "conv-test", "message": "سلام"},
            content_type="application/json",
        )
        self.assertEqual(conversation_response.status_code, 200)
        payload = conversation_response.json()

        history_response = self.client.get(
            "/api/history/?site_id=demo&conversation_id=conv-test"
        )
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.json()["messages"]), 2)

        feedback_response = self.client.post(
            "/api/feedback/",
            data={
                "site_id": "demo",
                "conversation_id": "conv-test",
                "message_id": payload["message_id"],
                "feedback": "helpful",
            },
            content_type="application/json",
        )
        self.assertEqual(feedback_response.status_code, 200)
