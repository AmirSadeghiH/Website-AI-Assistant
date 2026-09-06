"""Deployment-readiness tests.

Guards the PaaS (Railway) single-container flow:
- DATABASE_URL parsing (Railway injects one URL instead of five vars)
- production health endpoint answers without a widget key (healthcheck)
- corpus self-heal (ensure_deploy) on partial / corrupt artifacts
- inline worker spawning is skipped inside containers (memory safety)
"""

import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from config.settings import _database_url_options
from chat.document_pipeline import (
    enqueue_documents,
    should_spawn_inline_worker,
)
from chat.models import Document


class DatabaseUrlParsingTests(unittest.TestCase):
    """Pure-function tests for the one-variable database configuration."""

    def test_postgres_url_is_parsed(self):
        opts = _database_url_options(
            "postgres://user:p%40ss@db.host:6543/ai_support"
        )

        self.assertEqual(opts["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(opts["NAME"], "ai_support")
        self.assertEqual(opts["USER"], "user")
        self.assertEqual(opts["PASSWORD"], "p@ss")
        self.assertEqual(opts["HOST"], "db.host")
        self.assertEqual(opts["PORT"], "6543")

    def test_postgresql_scheme_alias(self):
        opts = _database_url_options("postgresql://u@h/mydb")

        self.assertEqual(opts["NAME"], "mydb")
        self.assertEqual(opts["PORT"], "5432")  # default

    def test_sqlite_url(self):
        opts = _database_url_options("sqlite:///path/to/db.sqlite3")

        self.assertEqual(opts["ENGINE"], "django.db.backends.sqlite3")

    def test_unsupported_scheme_raises(self):
        with self.assertRaises(Exception):
            _database_url_options("mysql://u@h/db")

    def test_default_database_is_sqlite_in_tests(self):
        from django.conf import settings

        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )


class ProductionHealthTests(TestCase):
    """The PaaS healthcheck must pass in strict production mode."""

    @override_settings(DEBUG=False, WIDGET_REQUIRE_KEY=True)
    def test_health_answers_without_widget_key_in_production_mode(self):
        response = Client().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        # Minimal public payload: booleans only, no version/config leaks.
        self.assertEqual(set(body["checks"].keys()), {"database", "corpus"})

    def test_corpus_paths_follow_settings(self):
        """document_pipeline + views derive paths from settings.CORPUS_DATA_DIR."""
        from django.conf import settings

        from chat.document_pipeline import CHUNKS_PATH, EMBEDDINGS_PATH, METADATA_PATH
        from chat.views import CORPUS_ARTIFACTS

        expected = Path(settings.CORPUS_DATA_DIR) / "chunks.json"
        self.assertEqual(CHUNKS_PATH, expected)
        self.assertEqual(
            METADATA_PATH, Path(settings.CORPUS_DATA_DIR) / "metadata.json"
        )
        self.assertEqual(
            EMBEDDINGS_PATH, Path(settings.CORPUS_DATA_DIR) / "embeddings.npy"
        )
        self.assertEqual(CORPUS_ARTIFACTS[0], expected)


class CorpusSelfHealTests(TestCase):
    """ensure_deploy repairs partial corpora instead of 503-forever.

    Runs against a temp directory via override_settings so the developer's
    real Data/ corpus is never touched by tests.
    """

    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp_path = Path(self._tmp.name)
        corpus_dir = tmp_path / "Data"
        corpus_dir.mkdir()
        # Pipeline paths are module-level constants bound at import time;
        # point them at the temp corpus for the duration of each test.
        patcher_chunk = mock.patch(
            "chat.document_pipeline.CHUNKS_PATH", corpus_dir / "chunks.json"
        )
        patcher_meta = mock.patch(
            "chat.document_pipeline.METADATA_PATH", corpus_dir / "metadata.json"
        )
        patcher_emb = mock.patch(
            "chat.document_pipeline.EMBEDDINGS_PATH", corpus_dir / "embeddings.npy"
        )
        patcher_dir = mock.patch(
            "chat.document_pipeline.settings.CORPUS_DATA_DIR", corpus_dir
        )
        for p in (patcher_chunk, patcher_meta, patcher_emb, patcher_dir):
            p.start()
            self.addCleanup(p.stop)
        self.corpus_dir = corpus_dir

    @property
    def _chunks(self):
        return self.corpus_dir / "chunks.json"

    @property
    def _metadata(self):
        return self.corpus_dir / "metadata.json"

    @property
    def _embeddings(self):
        return self.corpus_dir / "embeddings.npy"

    def _artifacts(self):
        return (self._chunks, self._metadata, self._embeddings)

    def _run(self):
        call_command(
            "ensure_deploy",
            "--no-collectstatic",
            "--skip-superuser",
            verbosity=0,
        )
    def test_fresh_install_no_crash(self):
        self._run()
        self.assertFalse(any(p.exists() for p in self._artifacts()))

    def test_partial_corpus_is_removed(self):
        self._chunks.write_text(json.dumps(["chunk"]), encoding="utf-8")

        self._run()

        self.assertFalse(any(p.exists() for p in self._artifacts()))

    def test_count_mismatch_clears_corpus(self):
        import numpy as np

        self._chunks.write_text(json.dumps(["a", "b", "c"]), encoding="utf-8")
        self._metadata.write_text(json.dumps([{}, {}, {}]), encoding="utf-8")
        np.save(self._embeddings, np.zeros((2, 3), dtype="float32"))

        self._run()

        self.assertFalse(any(p.exists() for p in self._artifacts()))

    def test_consistent_corpus_is_untouched(self):
        import numpy as np

        self._chunks.write_text(json.dumps(["a", "b"]), encoding="utf-8")
        self._metadata.write_text(json.dumps([{}, {}]), encoding="utf-8")
        np.save(self._embeddings, np.zeros((2, 3), dtype="float32"))

        self._run()

        self.assertTrue(all(p.exists() for p in self._artifacts()))


class WorkerSpawnPolicyTests(TestCase):
    """Container deploys must not spawn detached subprocesses."""

    @mock.patch.dict(os.environ, {"SPAWN_WORKERS": "0"})
    def test_explicit_off(self):
        self.assertFalse(should_spawn_inline_worker())

    @mock.patch.dict(os.environ, {"SPAWN_WORKERS": "1"})
    def test_explicit_on(self):
        self.assertTrue(should_spawn_inline_worker())

    @mock.patch.dict(os.environ, {"SPAWN_WORKERS": "auto", "CONTAINERIZED": "1"})
    def test_auto_disables_inside_container(self):
        self.assertFalse(should_spawn_inline_worker())

    @mock.patch.dict(
        os.environ, {"SPAWN_WORKERS": "auto", "CONTAINERIZED": "", "RAILWAY_ENVIRONMENT": ""}
    )
    def test_auto_enables_on_dev_machine(self):
        self.assertTrue(should_spawn_inline_worker())

    @mock.patch.dict(os.environ, {"SPAWN_WORKERS": "0"})
    def test_enqueue_documents_queues_without_spawning(self):
        document = Document.objects.create(
            title="deploy doc",
            status="ready",
            source_type="txt",
        )

        with mock.patch.object(subprocess, "Popen") as popen:
            count = enqueue_documents([document.pk])

        self.assertEqual(count, 1)
        popen.assert_not_called()
        document.refresh_from_db()
        self.assertEqual(document.status, "queued")
