"""Probe: simulate Railway environment variables and verify settings react."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.update(
    {
        "DEBUG": "False",
        "SECRET_KEY": "railway-sim-secret-key-not-real-1234567890abcdef",
        "DATABASE_URL": "postgres://postgres:secretpw@containers-us-west-1.railway.app:6543/railway",
        "REDIS_URL": "redis://default:pass@redis.railway.internal:6379/0",
        "RAILWAY_ENVIRONMENT": "production",
        "RAILWAY_PUBLIC_DOMAIN": "ai-support-production.up.railway.app",
        "PERSIST_DIR": "/data",
        "USE_WHITENOISE": "True",
        "WIDGET_REQUIRE_KEY": "True",
    }
)

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings  # noqa: E402

failures = []


def check(name, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {actual!r}")
    if not ok:
        failures.append(name)


check(
    "DATABASES from DATABASE_URL",
    (
        settings.DATABASES["default"]["ENGINE"],
        settings.DATABASES["default"]["NAME"],
        settings.DATABASES["default"]["HOST"],
        settings.DATABASES["default"]["PORT"],
    ),
    (
        "django.db.backends.postgresql",
        "railway",
        "containers-us-west-1.railway.app",
        "6543",
    ),
)
check(
    "ALLOWED_HOSTS includes railway domain",
    "ai-support-production.up.railway.app" in settings.ALLOWED_HOSTS,
    True,
)
check("TRUST_PROXY_SSL auto-on", settings.TRUST_PROXY_SSL, True)
check(
    "SECURE_PROXY_SSL_HEADER set",
    settings.SECURE_PROXY_SSL_HEADER,
    ("HTTP_X_FORWARDED_PROTO", "https"),
)
check(
    "CSRF_TRUSTED_ORIGINS includes railway",
    "https://ai-support-production.up.railway.app" in settings.CSRF_TRUSTED_ORIGINS,
    True,
)
check("MEDIA_ROOT under volume", settings.MEDIA_ROOT, __import__("pathlib").Path("/data") / "media")
check("CORPUS_DATA_DIR under volume", settings.CORPUS_DATA_DIR, __import__("pathlib").Path("/data") / "Data")
check(
    "whitenoise middleware active",
    any("whitenoise" in m for m in settings.MIDDLEWARE),
    True,
)
check("WIDGET_REQUIRE_KEY stays strict", settings.WIDGET_REQUIRE_KEY, True)

# document_pipeline + retriever must point at the volume
from chat.document_pipeline import CHUNKS_PATH  # noqa: E402
from chat.views import CORPUS_ARTIFACTS  # noqa: E402

check(
    "document_pipeline paths follow volume",
    str(CHUNKS_PATH),
    str(settings.CORPUS_DATA_DIR / "chunks.json"),
)
check(
    "health CORPUS_ARTIFACTS follow volume",
    str(CORPUS_ARTIFACTS[0]),
    str(settings.CORPUS_DATA_DIR / "chunks.json"),
)
check(
    "spawn workers skipped in container",
    __import__("chat.document_pipeline", fromlist=["x"]).should_spawn_inline_worker(),
    False,
)

print()
if failures:
    print(f"FAILED: {len(failures)} -> {failures}")
    sys.exit(1)
print("ALL RAILWAY-SETTING PROBES PASSED")
