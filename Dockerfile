# ─── AI Support Platform — Production Dockerfile (single container) ──────
# Everything runs in one container: web + background worker.
# Railway sets $PORT; locally it defaults to 8000.
#
# Build:  docker build -t ai-support-platform .
# Run:    docker run -p 8000:8000 --env-file .env ai-support-platform
# ──────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# Prevent Python from buffering stdout/stderr (critical for Docker logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_WHITENOISE=True \
    SPAWN_WORKERS=auto \
    CONTAINERIZED=1

WORKDIR /app

# Install system dependencies for faiss-cpu, pymupdf, psycopg2, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ─── Dependencies layer (cached unless requirements.txt changes) ─────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Application code ───────────────────────────────────────────────────
COPY . .

# collectstatic also runs inside ensure_deploy at start; a build-time pass
# keeps the whitenoise manifest valid even if the start command changes.
RUN SECRET_KEY=build-placeholder DEBUG=False python manage.py collectstatic \
    --noinput --clear >/dev/null 2>&1 || true

# Non-root user
RUN addgroup --system django && adduser --system --ingroup django django \
    && mkdir -p /app/Data /app/media /app/staticfiles \
    && chown -R django:django /app \
    && chmod +x /app/deploy/entrypoint.sh

USER django

EXPOSE 8000

# Lightweight unauthenticated liveness endpoint (no widget key needed).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:%s/api/health/' % os.environ.get('PORT','8000'))"

ENTRYPOINT ["/app/deploy/entrypoint.sh"]
