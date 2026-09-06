import io
import json
import zipfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import override_settings
from django.test import RequestFactory
from django.test import TestCase

from .admin import DocumentAdminForm, ProviderSettingsForm
from .document_pipeline import extract_docx, sniff_file_type
from .middleware import ApiRequestSizeLimitMiddleware, RequestMonitoringMiddleware
from .models import (
    AdminNotification,
    AnalyticsEvent,
    Document,
    ProviderSettings,
    WidgetConfig,
)


class ChatEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.config = WidgetConfig.objects.create(
            business_name="Demo business",
            title="دستیار آزمایشی",
            faq_url="https://example.com/faq/",
            privacy_url="https://example.com/privacy/",
            suggestions=["شرایط دریافت وام؟", "تماس با پشتیبانی"],
        )

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
        payload = response.json()
        self.assertEqual(payload["answer"], "پاسخ آزمایشی")
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        # Product v2 contract: conversations are persisted server-side and
        # the widget receives a conversation id + HMAC token + message id.
        self.assertIn("conversation_id", payload)
        self.assertTrue(payload["conversation_id"])
        self.assertIn("conversation_token", payload)
        self.assertIn("message_id", payload)
        self.assertIn("citations", payload)
        self.assertIn("intent", payload)
        get_rag_service.return_value.ask.assert_called_once()

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
        # Health is the PaaS liveness probe: must answer without a widget key.
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["mode"], "single-site")
        # No sensitive payload leaks through the open endpoint.
        body = response.json()
        self.assertEqual(set(body["checks"].keys()), {"database", "corpus"})

    @patch("chat.views.get_rag_service")
    def test_chat_maps_corpus_config_errors_to_503(self, get_rag_service):
        from .services import CorpusConfigError

        get_rag_service.side_effect = CorpusConfigError("inconsistent")

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "corpus_config")

    @patch("chat.views.get_rag_service")
    def test_chat_maps_embedding_mismatch_to_503(self, get_rag_service):
        from rag.retriever import EmbeddingDimensionMismatchError

        get_rag_service.side_effect = EmbeddingDimensionMismatchError(
            "dimension mismatch"
        )

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "corpus_config")

    @patch("chat.views.get_rag_service")
    def test_chat_falls_back_when_rag_returns_empty_answer(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "   "

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["answer"].strip())

    def test_api_body_size_middleware(self):
        factory = RequestFactory()
        ok_view = lambda request: HttpResponse("ok")
        middleware = ApiRequestSizeLimitMiddleware(ok_view)

        no_length = factory.post(
            "/api/chat/",
            data=b'{"message": "x"}',
            content_type="application/json",
        )
        del no_length.META["CONTENT_LENGTH"]
        response = middleware(no_length)
        self.assertEqual(response.status_code, 411)

        chunked = factory.post(
            "/api/chat/",
            data=b'{"message": "x"}',
            content_type="application/json",
            HTTP_TRANSFER_ENCODING="chunked",
        )
        response = middleware(chunked)
        self.assertEqual(response.status_code, 411)

        too_big = factory.post(
            "/api/chat/",
            data=b"x" * (64 * 1024 + 1),
            content_type="application/json",
        )
        response = middleware(too_big)
        self.assertEqual(response.status_code, 413)

        negative = factory.post(
            "/api/chat/",
            data=b"{}",
            content_type="application/json",
            CONTENT_LENGTH="-5",
        )
        response = middleware(negative)
        self.assertEqual(response.status_code, 413)

        ok_request = factory.post(
            "/api/chat/",
            data=b'{"message": "x"}',
            content_type="application/json",
        )
        response = middleware(ok_request)
        self.assertEqual(response.status_code, 200)

    def test_provider_settings_encrypts_keys_at_rest(self):
        provider = ProviderSettings.objects.create(
            llm_api_key="sk-secret-llm",
            embedding_api_key="sk-secret-embed",
        )

        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT llm_api_key, embedding_api_key "
                "FROM chat_providersettings WHERE id = %s",
                [provider.pk],
            )
            raw = cursor.fetchone()
        self.assertTrue(raw[0].startswith("enc:v1:"))
        self.assertNotIn("sk-secret-llm", raw[0])
        self.assertNotIn("sk-secret-embed", raw[1])

        reloaded = ProviderSettings.objects.get(pk=provider.pk)
        self.assertEqual(reloaded.llm_api_key, "sk-secret-llm")
        self.assertEqual(reloaded.embedding_api_key, "sk-secret-embed")

    @patch("chat.services.Retriever")
    @patch("chat.services.OpenRouterLLM")
    @patch("chat.services.Embedder")
    def test_rag_service_uses_provider_settings(self, embedder_cls, llm_cls, _retriever_cls):
        from .services import RAGService

        service = RAGService(
            provider={
                "llm_api_key": "sk-llm",
                "llm_base_url": "https://llm.example/v1",
                "llm_model": "model-x",
                "llm_max_tokens": 500,
                "llm_timeout_seconds": 12.0,
                "llm_max_retries": 1,
                "embedding_api_key": "sk-emb",
                "embedding_base_url": "https://emb.example/v1",
                "embedding_model": "embed-x",
                "embedding_timeout_seconds": 9.0,
                "embedding_max_retries": 0,
                "rag_max_concurrent": 4,
                "response_cache_seconds": 30,
            }
        )
        self.assertEqual(service.cache_seconds, 30)
        llm_kwargs = llm_cls.call_args.kwargs
        self.assertEqual(llm_kwargs["api_key"], "sk-llm")
        self.assertEqual(llm_kwargs["model"], "model-x")
        self.assertEqual(llm_kwargs["base_url"], "https://llm.example/v1")
        self.assertEqual(llm_kwargs["timeout"], 12.0)
        self.assertEqual(llm_kwargs["max_retries"], 1)
        self.assertEqual(llm_kwargs["max_tokens"], 500)
        embed_kwargs = embedder_cls.call_args.kwargs
        self.assertEqual(embed_kwargs["api_key"], "sk-emb")
        self.assertEqual(embed_kwargs["model_name_api"], "embed-x")
        self.assertEqual(embed_kwargs["timeout"], 9.0)

    def test_provider_values_override_env(self):
        import os

        os.environ["LLM_MODEL"] = "env-model"
        os.environ["EMBEDDING_MODEL"] = "env-embed"
        ProviderSettings.objects.create(
            llm_model="admin-model",
            embedding_model="admin-embed",
        )
        try:
            from .services import get_provider_values

            values = get_provider_values()
            self.assertEqual(values["llm_model"], "admin-model")
            self.assertEqual(values["embedding_model"], "admin-embed")
        finally:
            os.environ.pop("LLM_MODEL", None)
            os.environ.pop("EMBEDDING_MODEL", None)

    def test_widget_config_endpoint(self):
        config_response = self.client.get("/api/widget-config/")
        self.assertEqual(config_response.status_code, 200)
        self.assertEqual(config_response.json()["business_name"], "Demo business")
        self.assertEqual(config_response.json()["suggestions"], self.config.suggestions)
        self.assertEqual(config_response.json()["panel_width"], 400)
        self.assertEqual(config_response.json()["show_timestamp"], True)

    def test_events_create_analytics(self):
        response = self.client.post(
            "/api/events/",
            data={
                "event_type": "widget_loaded",
                "metadata": {"version": "beta"},
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AnalyticsEvent.objects.filter(event_type="widget_loaded").exists(),
        )

    def test_widget_config_is_singleton(self):
        response = self.client.get("/api/widget-config/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(WidgetConfig.objects.count(), 1)

    @override_settings(
        WIDGET_PUBLIC_KEY="test-public-key",
        WIDGET_ALLOWED_ORIGINS=("https://carsanj.ir",),
    )
    def test_widget_key_enforces_access(self):
        headers = {
            "HTTP_X_WIDGET_KEY": "test-public-key",
            "HTTP_ORIGIN": "https://carsanj.ir",
        }

        allowed = self.client.get("/api/widget-config/", **headers)
        self.assertEqual(allowed.status_code, 200)

        denied = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wrong",
            HTTP_ORIGIN="https://carsanj.ir",
        )
        self.assertEqual(denied.status_code, 403)

    @override_settings(
        WIDGET_PUBLIC_KEY="",
        WIDGET_ALLOWED_ORIGINS=(),
    )
    def test_panel_managed_key_and_origins_enforce_access(self):
        ProviderSettings.objects.create(
            widget_public_key="panel-key",
            widget_allowed_origins="https://panel.example\nhttps://www.panel.example",
        )

        allowed = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="panel-key",
            HTTP_ORIGIN="https://panel.example",
        )
        self.assertEqual(allowed.status_code, 200)

        wrong_key = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wrong",
            HTTP_ORIGIN="https://panel.example",
        )
        self.assertEqual(wrong_key.status_code, 403)

        wrong_origin = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="panel-key",
            HTTP_ORIGIN="https://evil.example",
        )
        self.assertEqual(wrong_origin.status_code, 403)

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=(),
    )
    @patch("chat.views.get_rag_service")
    def test_panel_origins_enable_cors(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ"
        ProviderSettings.objects.create(
            widget_allowed_origins="https://panel.example",
        )

        response = self.client.post(
            "/api/chat/",
            data={"message": "سلام"},
            content_type="application/json",
            HTTP_ORIGIN="https://panel.example",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://panel.example",
        )

    @override_settings(
        CORS_ALLOW_ALL_ORIGINS=False,
        CORS_ALLOWED_ORIGINS=(),
    )
    def test_panel_origins_allow_preflight(self):
        ProviderSettings.objects.create(
            widget_allowed_origins="https://panel.example",
        )

        response = self.client.options(
            "/api/chat/",
            HTTP_ORIGIN="https://panel.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type, x-widget-key",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://panel.example",
        )

    def test_widget_access_config_falls_back_to_env(self):
        from .api_permissions import get_widget_access_config

        with override_settings(
            WIDGET_PUBLIC_KEY="env-key",
            WIDGET_ALLOWED_ORIGINS=("https://env.example",),
        ):
            widget_key, origins = get_widget_access_config()
            self.assertEqual(widget_key, "env-key")
            self.assertEqual(origins, ("https://env.example",))

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


class MonitoringTests(TestCase):
    def test_request_monitoring_creates_notification_on_errors(self):
        factory = RequestFactory()

        def error_view(request):
            from django.http import HttpResponseServerError
            return HttpResponseServerError()

        middleware = RequestMonitoringMiddleware(error_view)

        # Simulate 11 requests in the same minute window
        for i in range(11):
            request = factory.post("/api/test/")
            middleware(request)

        self.assertTrue(
            AdminNotification.objects.filter(
                title="Error rate spike detected",
                severity="critical",
            ).exists()
        )

    def test_mark_notifications_read_via_admin(self):
        AdminNotification.objects.create(
            title="Test alert",
            message="Something happened",
            severity="warning",
        )
        self.assertEqual(AdminNotification.objects.filter(is_read=False).count(), 1)

        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="safe-password-123",
        )
        self.client.force_login(user)

        response = self.client.post("/admin/notifications-mark-read/")
        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(AdminNotification.objects.filter(is_read=False).count(), 0)

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
        self.assertContains(response, "CONTROL ROOM")
        self.assertContains(response, "Widget settings")
        self.assertContains(response, "Knowledge documents")
        self.assertContains(response, "نوتیفیکیشن‌ها")

        form_response = self.client.get("/admin/chat/document/add/")
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, "PDF")
        self.assertContains(form_response, "DOCX")

        provider_form = self.client.get("/admin/chat/providersettings/add/")
        self.assertEqual(provider_form.status_code, 200)
        self.assertContains(provider_form, "نصب ویجت و کنترل دسترسی")
        self.assertContains(provider_form, "widget_allowed_origins")

    def test_provider_settings_form_normalizes_origins(self):
        form = ProviderSettingsForm(
            data={
                "widget_public_key": "install-key",
                "widget_allowed_origins": (
                    " https://a.example/ \nhttps://b.example\nhttps://a.example"
                ),
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(
            instance.allowed_origins_list,
            ["https://a.example", "https://b.example"],
        )
        reloaded = ProviderSettings.objects.get(pk=instance.pk)
        self.assertEqual(reloaded.widget_public_key, "install-key")

    def test_provider_settings_form_rejects_bad_origins(self):
        form = ProviderSettingsForm(
            data={
                "widget_allowed_origins": "https://ok.example\nnot-a-url",
            }
        )
        self.assertFalse(form.is_valid())

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

    def test_docx_zip_bomb_is_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", b"A" * (33 * 1024 * 1024))
        buffer.seek(0)

        with self.assertRaisesRegex(ValueError, "بیش از حد"):
            extract_docx(buffer)

    def test_docx_xml_entity_expansion_is_blocked(self):
        import io

        evil = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]>'
            b"<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            b"<w:body><w:p><w:r><w:t>&lol2;</w:t></w:r></w:p></w:body></w:document>"
        )
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("word/document.xml", evil)
        buffer.seek(0)
        with self.assertRaises(Exception):
            extract_docx(buffer)

    def test_sniff_file_type_matches_content_not_extension(self):
        import os
        import shutil
        import uuid
        from pathlib import Path

        tmp = Path(
            os.path.join(
                os.environ.get("TEMP", "."), f"sniff-test-{uuid.uuid4().hex[:8]}"
            )
        )
        os.makedirs(tmp, exist_ok=True)
        try:
            fake_pdf = tmp / "fake.pdf"
            fake_pdf.write_bytes(b"#!/bin/sh\nrm -rf /\n")
            self.assertEqual(sniff_file_type(fake_pdf), "txt")

            real_pdf = tmp / "real.txt"
            real_pdf.write_bytes(b"%PDF-1.4 not really but signature matches")
            self.assertEqual(sniff_file_type(real_pdf), "pdf")

            binary = tmp / "bin.txt"
            binary.write_bytes(b"\x00\x01\x02binary\x00")
            self.assertIsNone(sniff_file_type(binary))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_retriever_raises_clear_error_on_dimension_mismatch(self):
        import os
        import shutil
        import uuid
        from pathlib import Path

        import numpy as np

        from rag.retriever import EmbeddingDimensionMismatchError, Retriever

        class FakeEmbedder:
            def embed_query_api(self, query):
                return np.zeros(8, dtype="float32")

        tmp = Path(
            os.path.join(
                os.environ.get("TEMP", "."), f"retriever-test-{uuid.uuid4().hex[:8]}"
            )
        )
        os.makedirs(tmp, exist_ok=True)
        try:
            (tmp / "chunks.json").write_text(
                json.dumps(["متن یک", "متن دو"], ensure_ascii=False),
                encoding="utf-8",
            )
            (tmp / "metadata.json").write_text(
                json.dumps([{"doc_id": "a"}, {"doc_id": "b"}]),
                encoding="utf-8",
            )
            np.save(tmp / "embeddings.npy", np.zeros((2, 4), dtype="float32"))

            retriever = Retriever(
                chunks_path=str(tmp / "chunks.json"),
                metadata_path=str(tmp / "metadata.json"),
                embeddings_path=str(tmp / "embeddings.npy"),
                embedder=FakeEmbedder(),
            )
            with self.assertRaises(EmbeddingDimensionMismatchError):
                retriever.retrieve("سؤال")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_retriever_empty_corpus_returns_no_results(self):
        import os
        import shutil
        import uuid
        from pathlib import Path

        from rag.retriever import Retriever

        tmp = Path(
            os.path.join(
                os.environ.get("TEMP", "."), f"corpus-test-{uuid.uuid4().hex[:8]}"
            )
        )
        os.makedirs(tmp, exist_ok=True)
        try:
            retriever = Retriever(
                chunks_path=str(tmp / "chunks.json"),
                metadata_path=str(tmp / "metadata.json"),
                embeddings_path=str(tmp / "embeddings.npy"),
            )
            self.assertEqual(retriever.retrieve("هر سؤالی"), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

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
                "action": "process_documents_action",
                "_selected_action": [str(document.pk)],
                "index": 0,
                "select_across": 0,
            },
        )
        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.status, "queued")
        popen.assert_called_once()


class FeedbackEndpointTests(TestCase):
    """Tests for the /api/feedback/ endpoint."""

    def setUp(self):
        cache.clear()
        WidgetConfig.objects.create(business_name="Test")

    def test_feedback_thumbs_up_is_persisted(self):
        response = self.client.post(
            "/api/feedback/",
            data={
                "helpful": True,
                "question": "چطور حساب باز کنم؟",
                "answer_preview": "برای باز کردن حساب...",
                "session_id": "abc-123",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        event = AnalyticsEvent.objects.filter(event_type="answer_helpful").last()
        self.assertIsNotNone(event)
        self.assertEqual(event.metadata["question"], "چطور حساب باز کنم؟")
        self.assertEqual(event.metadata["session_id"], "abc-123")

    def test_feedback_thumbs_down_is_persisted(self):
        response = self.client.post(
            "/api/feedback/",
            data={"helpful": False, "question": "سؤال بد"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AnalyticsEvent.objects.filter(event_type="answer_not_helpful").exists())

    def test_feedback_with_comment(self):
        response = self.client.post(
            "/api/feedback/",
            data={
                "helpful": True,
                "question": "test",
                "comment": "عالی بود!",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        event = AnalyticsEvent.objects.filter(event_type="answer_helpful").last()
        self.assertEqual(event.metadata["comment"], "عالی بود!")

    def test_feedback_rejects_missing_helpful_field(self):
        response = self.client.post(
            "/api/feedback/",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_feedback_rejects_invalid_payload(self):
        response = self.client.post(
            "/api/feedback/",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class OriginMatchingTests(TestCase):
    """Test wildcard and exact origin matching."""

    def test_exact_match(self):
        from .api_permissions import _origin_matches
        self.assertTrue(_origin_matches("https://example.com", ["https://example.com"]))

    def test_exact_mismatch(self):
        from .api_permissions import _origin_matches
        self.assertFalse(_origin_matches("https://example.com", ["https://other.com"]))

    def test_wildcard_subdomain_match(self):
        from .api_permissions import _origin_matches
        self.assertTrue(_origin_matches("https://shop.example.com", ["https://*.example.com"]))

    def test_wildcard_subdomain_mismatch(self):
        from .api_permissions import _origin_matches
        self.assertFalse(_origin_matches("https://evil-example.com", ["https://*.example.com"]))

    def test_wildcard_does_not_match_bare_domain(self):
        from .api_permissions import _origin_matches
        self.assertFalse(_origin_matches("https://example.com", ["https://*.example.com"]))

    def test_case_insensitive(self):
        from .api_permissions import _origin_matches
        self.assertTrue(_origin_matches("https://A.Example.COM", ["https://a.example.com"]))

    def test_empty_origin_fails(self):
        from .api_permissions import _origin_matches
        self.assertFalse(_origin_matches("", ["https://example.com"]))

    def test_multiple_patterns(self):
        from .api_permissions import _origin_matches
        patterns = ["https://other.com", "https://*.example.com"]
        self.assertTrue(_origin_matches("https://shop.example.com", patterns))
        self.assertFalse(_origin_matches("https://evil.com", patterns))

    @override_settings(
        WIDGET_PUBLIC_KEY="wk",
        WIDGET_ALLOWED_ORIGINS=("https://*.example.com",),
    )
    def test_wildcard_origin_allows_subdomains_via_api(self):
        allowed = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wk",
            HTTP_ORIGIN="https://shop.example.com",
        )
        self.assertEqual(allowed.status_code, 200)

        denied = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wk",
            HTTP_ORIGIN="https://evil.attacker.com",
        )
        self.assertEqual(denied.status_code, 403)

    @override_settings(
        WIDGET_PUBLIC_KEY="wk",
        WIDGET_ALLOWED_ORIGINS=("https://example.com",),
    )
    def test_referer_fallback_when_origin_missing(self):
        """When Origin header is absent, Referer is used as fallback."""
        allowed = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wk",
            HTTP_REFERER="https://example.com/page",
        )
        self.assertEqual(allowed.status_code, 200)

        denied = self.client.get(
            "/api/widget-config/",
            HTTP_X_WIDGET_KEY="wk",
            HTTP_REFERER="https://evil.com/page",
        )
        self.assertEqual(denied.status_code, 403)


@override_settings(DEBUG=True)
class MediaDocumentProtectionTests(TestCase):
    """Test that uploaded source documents cannot be accessed directly."""

    def test_media_documents_returns_404(self):
        from .middleware import MediaDocumentProtectionMiddleware

        factory = RequestFactory()
        ok_view = lambda request: HttpResponse("ok")
        middleware = MediaDocumentProtectionMiddleware(ok_view)

        request = factory.get("/media/documents/2026/08/guide.pdf")
        from django.http import Http404
        with self.assertRaises(Http404):
            middleware(request)

    def test_other_media_paths_pass_through(self):
        from .middleware import MediaDocumentProtectionMiddleware

        factory = RequestFactory()
        ok_view = lambda request: HttpResponse("ok")
        middleware = MediaDocumentProtectionMiddleware(ok_view)

        request = factory.get("/media/avatars/user.png")
        response = middleware(request)
        self.assertEqual(response.status_code, 200)


class AdminAnalyticsApiTests(TestCase):
    """Tests for the analytics and FAQ leaderboard API endpoints."""

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="analyst",
            email="a@b.com",
            password="pass-1234",
        )
        self.client.force_login(self.user)

    def test_analytics_data_requires_staff(self):
        self.client.logout()
        response = self.client.get("/admin/analytics-data/")
        self.assertIn(response.status_code, (302, 403))

    def test_analytics_data_returns_structure(self):
        AnalyticsEvent.objects.create(event_type="assistant_answered", metadata={"latency_ms": 120})
        AnalyticsEvent.objects.create(event_type="assistant_answered", metadata={"latency_ms": 200})
        AnalyticsEvent.objects.create(event_type="error_occurred")
        AnalyticsEvent.objects.create(event_type="widget_loaded")
        AnalyticsEvent.objects.create(event_type="answer_helpful", metadata={"question": "سؤال تست"})

        response = self.client.get("/admin/analytics-data/?period=day&days=30")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("messages", data)
        self.assertIn("errors", data)
        self.assertIn("loads", data)
        self.assertIn("helpful", data)
        self.assertIn("total_messages", data)
        self.assertEqual(data["total_messages"], 2)
        self.assertEqual(data["total_errors"], 1)
        self.assertEqual(data["helpful"], 1)

    def test_faq_leaderboard_requires_staff(self):
        self.client.logout()
        response = self.client.get("/admin/faq-leaderboard/")
        self.assertIn(response.status_code, (302, 403))


