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
from .middleware import ApiRequestSizeLimitMiddleware
from .models import (
    AnalyticsEvent,
    Conversation,
    Document,
    Message,
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
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    @patch("chat.views.get_rag_service")
    def test_history_is_limited_to_100_messages(self, get_rag_service):
        get_rag_service.return_value.ask.return_value = "پاسخ آزمایشی"
        conversation = Conversation.objects.create(external_id="long-conv")
        for index in range(120):
            Message.objects.create(
                conversation=conversation,
                role="user" if index % 2 == 0 else "assistant",
                content=f"message-{index}",
            )

        response = self.client.get("/api/history/?conversation_id=long-conv")

        self.assertEqual(response.status_code, 200)
        messages = response.json()["messages"]
        self.assertEqual(len(messages), 100)
        # Oldest retained message is the 20th; the newest is the last one.
        self.assertEqual(messages[0]["content"], "message-20")
        self.assertEqual(messages[-1]["content"], "message-119")

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
        self.assertIn(
            "x-widget-key",
            response.headers.get("Access-Control-Allow-Headers", ""),
        )
        self.assertIn(
            "POST",
            response.headers.get("Access-Control-Allow-Methods", ""),
        )

    @override_settings(
        WIDGET_PUBLIC_KEY="",
        WIDGET_ALLOWED_ORIGINS=(),
    )
    def test_conversation_tokens_enforced_with_panel_key(self):
        ProviderSettings.objects.create(
            widget_public_key="panel-key",
            widget_allowed_origins="https://panel.example",
        )
        headers = {
            "HTTP_X_WIDGET_KEY": "panel-key",
            "HTTP_ORIGIN": "https://panel.example",
        }

        event = self.client.post(
            "/api/events/",
            data={"conversation_id": "panel-conv", "event_type": "widget_loaded"},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(event.status_code, 200)
        token = event.json()["conversation_token"]

        denied = self.client.get(
            "/api/history/?conversation_id=panel-conv",
            **headers,
        )
        self.assertEqual(denied.status_code, 403)

        allowed = self.client.get(
            "/api/history/?conversation_id=panel-conv",
            HTTP_X_WIDGET_KEY="panel-key",
            HTTP_X_CONVERSATION_TOKEN=token,
            HTTP_ORIGIN="https://panel.example",
        )
        self.assertEqual(allowed.status_code, 200)

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
        self.assertContains(response, "کلیدها و مدل‌های AI")

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
        import tempfile
        from pathlib import Path

        evil = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]>'
            b"<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            b"<w:body><w:p><w:r><w:t>&lol2;</w:t></w:r></w:p></w:body></w:document>"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evil.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", evil)
            with self.assertRaises(Exception):
                extract_docx(path)

    def test_sniff_file_type_matches_content_not_extension(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fake_pdf = tmp / "fake.pdf"
            fake_pdf.write_bytes(b"#!/bin/sh\nrm -rf /\n")
            self.assertEqual(sniff_file_type(fake_pdf), "txt")

            real_pdf = tmp / "real.txt"
            real_pdf.write_bytes(b"%PDF-1.4 not really but signature matches")
            self.assertEqual(sniff_file_type(real_pdf), "pdf")

            binary = tmp / "bin.txt"
            binary.write_bytes(b"\x00\x01\x02binary\x00")
            self.assertIsNone(sniff_file_type(binary))

    def test_retriever_raises_clear_error_on_dimension_mismatch(self):
        import tempfile
        from pathlib import Path

        import numpy as np

        from rag.retriever import EmbeddingDimensionMismatchError, Retriever

        class FakeEmbedder:
            def embed_query_api(self, query):
                return np.zeros(8, dtype="float32")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
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

    def test_retriever_empty_corpus_returns_no_results(self):
        import tempfile
        from pathlib import Path

        from rag.retriever import Retriever

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            retriever = Retriever(
                chunks_path=str(tmp / "chunks.json"),
                metadata_path=str(tmp / "metadata.json"),
                embeddings_path=str(tmp / "embeddings.npy"),
            )
            self.assertEqual(retriever.retrieve("هر سؤالی"), [])

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
