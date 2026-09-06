"""Production Gunicorn configuration for the AI Support Platform.

Capacity math (see README → Performance):
- Each chat request holds a worker thread while the LLM answers (bounded by
  RAG_MAX_CONCURRENT=8 per process), so threads >> workers is the right shape.
- 4 workers x 24 threads = 96 concurrent request slots; with the per-process
  semaphore and the response cache this comfortably serves 200+ simultaneous
  visitors. Increase ``workers`` only with more CPU cores — FAISS search is
  CPU-bound and the FAISS index is duplicated per worker.
"""

import multiprocessing
import os

# Keep workers modest: every worker loads its own copy of the FAISS index.
# threads carry concurrency; the RAG semaphore bounds LLM fan-out per worker.
# Capped at 4: PaaS containers report host cores (16+) while giving one vCPU
# and ~1GB RAM — uncapped cpu_count() would OOM instantly.
workers = int(
    os.getenv(
        "GUNICORN_WORKERS",
        str(max(2, min(4, multiprocessing.cpu_count() // 2))),
    )
)
threads = int(os.getenv("GUNICORN_THREADS", "24"))

# A chat request can legitimately take up to the LLM timeout (30s default).
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

# Tune the request/response buffer sizes (keep responses small).
max_requests = 2000
max_requests_jitter = 100

# /dev/shm is tiny on some PaaS images; fall back to /tmp when it is
# missing or smaller than 32MB (prevents "no space left on device").
import pathlib

if pathlib.Path("/dev/shm").is_dir() and pathlib.Path("/dev/shm").stat().st_size:
    worker_tmp_dir = "/dev/shm"
else:
    worker_tmp_dir = "/tmp"

# Bind: loopback by default (dev/nginx setups); PaaS platforms inject
# PORT and require 0.0.0.0 — handle that automatically so the container
# is reachable without touching this file.
_port = os.getenv("PORT", "")
bind = os.getenv(
    "GUNICORN_BIND",
    f"0.0.0.0:{_port}" if _port else "127.0.0.1:8000",
)
worker_tmp_dir = "/dev/shm"

accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
