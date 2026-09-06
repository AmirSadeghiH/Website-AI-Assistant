#!/bin/sh
# ─── Unified single-container entrypoint ─────────────────────────────────
# Runs ONE container that does everything (Railway-friendly):
#   1. migrate + collectstatic + corpus repair (idempotent)
#   2. background worker loop (crawl + document processing)
#   3. gunicorn on 0.0.0.0:$PORT
#
# No second service, no reverse proxy, no TLS config needed.
# ──────────────────────────────────────────────────────────────────────────
set -e

echo "[entrypoint] preparing deployment…"

# First boot: the managed database (Railway Postgres) may still be
# booting. Retry migrate a few times before giving up.
attempt=1
until python manage.py ensure_deploy --no-collectstatic; do
  if [ "$attempt" -ge 5 ]; then
    echo "[entrypoint] database not ready after 5 attempts — failing"
    exit 1
  fi
  echo "[entrypoint] migrate attempt $attempt failed, retrying in 5s…"
  attempt=$((attempt + 1))
  sleep 5
done

echo "[entrypoint] collecting static files"
python manage.py collectstatic --noinput --clear >/dev/null

echo "[entrypoint] starting background worker loop"
python manage.py runworker --loop --interval 5 &
WORKER_PID=$!

# Stop the worker when gunicorn exits (or the container gets a signal).
cleanup() {
  kill "$WORKER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[entrypoint] starting gunicorn on 0.0.0.0:${PORT:-8000}"
exec gunicorn config.wsgi:application \
  -c gunicorn.conf.py \
  --bind "0.0.0.0:${PORT:-8000}"
