from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import TestCase

from .admin import DocumentAdminForm
from .models import AnalyticsEvent, Conversation, Document, Message, WidgetConfig


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
        self.assertEqual(config_response.json()["panel_width"], 380)
        self.assertEqual(config_response.json()["mobile_fullscreen"], True)

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

    @override_settings(
        WIDGET_PUBLIC_KEY="test-public-key",
        WIDGET_ALLOWED_ORIGINS=("https://carsanj.ir",),
    )
    @patch("chat.views.get_rag_service")
    def test_widget_key_and_conversation_token_protect_history(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ امن"
        headers = {
            "HTTP_X_WIDGET_KEY": "test-public-key",
            "HTTP_ORIGIN": "https://carsanj.ir",
        }

        event = self.client.post(
            "/api/events/",
            data={"conversation_id": "secure-conv", "event_type": "widget_loaded"},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(event.status_code, 200)
        token = event.json()["conversation_token"]

        denied = self.client.get(
            "/api/history/?conversation_id=secure-conv",
            **headers,
        )
        self.assertEqual(denied.status_code, 403)

        allowed = self.client.get(
            "/api/history/?conversation_id=secure-conv",
            HTTP_X_WIDGET_KEY="test-public-key",
            HTTP_X_CONVERSATION_TOKEN=token,
            HTTP_ORIGIN="https://carsanj.ir",
        )
        self.assertEqual(allowed.status_code, 200)

    @override_settings(
        WIDGET_PUBLIC_KEY="test-public-key",
        WIDGET_ALLOWED_ORIGINS=("https://carsanj.ir",),
    )
    def test_wrong_widget_key_and_origin_are_rejected(self):
        wrong_key = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wrong",
            HTTP_ORIGIN="https://carsanj.ir",
        )
        self.assertEqual(wrong_key.status_code, 403)

        wrong_origin = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="test-public-key",
            HTTP_ORIGIN="https://attacker.example",
        )
        self.assertEqual(wrong_origin.status_code, 403)


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
        self.assertContains(response, "BETA CONTROL ROOM")
        self.assertContains(response, "Widget settings")
        self.assertContains(response, "Knowledge documents")

        form_response = self.client.get("/admin/chat/document/add/")
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, "PDF")
        self.assertContains(form_response, "DOCX")

    def test_document_form_accepts_supported_files_and_rejects_unknown_types(self):
        valid_form = DocumentAdminForm(
            data={"title": "راهنما"},
            files={
                "file": SimpleUploadedFile(
                    "guide.docx",
                    b"fake-docx",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
            },
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)

        invalid_form = DocumentAdminForm(
            data={"title": "اسکریپت"},
            files={
                "file": SimpleUploadedFile(
                    "script.exe",
                    b"not allowed",
                    content_type="application/octet-stream",
                ),
            },
        )
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("file", invalid_form.errors)

    @patch("chat.document_pipeline.subprocess.Popen")
    def test_document_admin_action_queues_background_worker(self, popen):
        user = get_user_model().objects.create_superuser(
            username="processor",
            email="processor@example.com",
            password="safe-password-123",
        )
        self.client.force_login(user)
        document = Document.objects.create(
            title="راهنما",
            file=SimpleUploadedFile("guide.txt", b"hello"),
            file_type="txt",
        )

        response = self.client.post(
            "/admin/chat/document/",
            {
                "action": "process_documents",
                "_selected_action": [str(document.pk)],
                "index": 0,
                "select_across": 0,
            },
        )
        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.status, "queued")
        popen.assert_called_once()
