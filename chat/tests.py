from unittest.mock import patch

from django.test import TestCase


class ChatEndpointTests(TestCase):
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
        self.assertEqual(response.json(), {"answer": "پاسخ آزمایشی"})
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
