# -*- coding: utf-8 -*-
"""Secret-scan guard test: the repo must never carry real credentials.

Verifies the release-gate requirement "no production secret was introduced"
in a form that fails loudly on every future regression run.
"""
import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import SimpleTestCase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File globs that must never contain secret-shaped literals.
SCAN_GLOBS = ["*.py", "*.js", "*.html", "*.md", "*.yml", "*.yaml", "*.json", "*.cfg"]
SCAN_DIRS = ["chat", "config", "rag", "scripts", "loadtest"]

SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9]{16,}", "OpenAI-style API key"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub PAT"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT"),
    (r"xox[bp]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"AIza[0-9A-Za-z_\-]{30,}", "Google API key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
]

# Allowed: the Django dev-only SECRET_KEY fallback in config/settings.py
# (clearly marked django-insecure-dev-only) and test fixtures with obviously
# fake values in chat/tests*.py.
ALLOW_MARKERS = ("django-insecure-dev-only", "safe-password", "sk-secret-llm",
                 "sk-secret-embed", "pw12345", "pass-1234", "replace-with",
                 "your-llm-api-key", "your-embedding-api-key", "forged-token")


def _iter_scan_files():
    for sub in SCAN_DIRS:
        root = os.path.join(BASE_DIR, sub)
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if any(name.endswith(g.lstrip("*")) for g in SCAN_GLOBS):
                    yield os.path.join(dirpath, name)


class SecretScanTest(SimpleTestCase):
    """Repo-wide scan: secret-shaped literals are release blockers."""

    def test_no_secret_shaped_literals_in_source(self):
        offenders = []
        for path in _iter_scan_files():
            with open(path, encoding="utf-8", errors="ignore") as fh:
                for lineno, line in enumerate(fh, start=1):
                    if any(marker in line for marker in ALLOW_MARKERS):
                        continue
                    for pattern, label in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            rel = os.path.relpath(path, BASE_DIR)
                            offenders.append(f"{rel}:{lineno} ({label})")
        self.assertEqual(
            offenders, [],
            "Secret-shaped literals found — these block release:\n"
            + "\n".join(offenders),
        )

    def test_no_private_key_files_on_disk(self):
        bad = []
        for dirpath, _dirs, files in os.walk(BASE_DIR):
            if any(part in (".git", ".venv", "staticfiles", "node_modules", ".freebuff") for part in dirpath.split(os.sep)):
                continue
            for name in files:
                if name in (".env", ".env.local", ".env.production"):
                    continue  # allowed but must be gitignored (next test)
                if name.endswith((".pem", ".key")) or name.startswith(("id_rsa", "id_ed25519")):
                    bad.append(os.path.relpath(os.path.join(dirpath, name), BASE_DIR))
        self.assertEqual(bad, [], f"Private key files present: {bad}")

    def test_env_is_gitignored(self):
        with open(os.path.join(BASE_DIR, ".gitignore"), encoding="utf-8") as fh:
            gitignore = fh.read()
        self.assertIn(".env", gitignore)
        self.assertIn("*.zip", gitignore, "Archives can hide .env copies — keep ignored")
