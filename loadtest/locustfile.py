# ─── Load testing: AI Support Platform (locustfile) ────────────────────────
# Run (after `pip install locust`):
#   locust -f loadtest/locustfile.py --host http://127.0.0.1:8000 --headless \
#          --users 50 --spawn-rate 5 --run-time 3m
#
# Escalation ladder used for the report: 10 → 50 → 100 → 200 users.
#
# NOTE: set WIDGET_REQUIRE_KEY=False (or export the right key) on the target
# before running. Never point this at a customer site.
# ──────────────────────────────────────────────────────────────────────────

import json
import random

from locust import HttpUser, between, events, task


QUESTION_POOL = [
    "شرایط دریافت وام چیه؟",
    "قیمت اشتراک چقدره؟",
    "چطور با پشتیبانی تماس بگیرم؟",
    "ساعات کاری مجموعه چیه؟",
    "وضعیت سفارش من رو بگید",
    "می‌خوام همکاری تجاری داشته باشم",
    "امکان مرجوعی کالا وجود داره؟",
    "سلام",
]

# Health endpoint must never be rate-limited; keep chat share moderate so
# the RAG semaphore (not the load generator) is the bottleneck we measure.
TASK_WEIGHTS = {"chat": 5, "widget_config": 3, "health": 1, "stream": 2}


class VisitorUser(HttpUser):
    wait_time = between(1.0, 3.0)

    def on_start(self):
        self.conversation_id = ""
        self.conversation_token = ""

    @task
    def health(self):
        self.client.get("/api/health/", name="[light] health")

    @task
    def widget_config(self):
        self.client.get("/api/widget-config/", name="[light] widget-config")

    @task
    def chat(self):
        payload = {
            "message": random.choice(QUESTION_POOL),
            "page_url": "https://loadtest.example/product/1",
        }
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        with self.client.post(
            "/api/chat/",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            name="[heavy] chat (RAG)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.conversation_id = data.get("conversation_id", "")
                self.conversation_token = data.get("conversation_token", "")
                if not data.get("answer"):
                    response.failure("empty answer")
            elif response.status_code == 429:
                response.success()  # throttled as designed — not an SLO breach

    @task
    def stream(self):
        payload = {
            "message": random.choice(QUESTION_POOL),
            "page_url": "https://loadtest.example/product/2",
        }
        if self.conversation_id:
            payload["conversation_id"] = self.conversation_id
        with self.client.post(
            "/api/chat/stream/",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            name="[heavy] chat stream (SSE)",
            catch_response=True,
            stream=True,
        ) as response:
            if response.status_code == 429:
                response.success()
                return
            if response.status_code != 200:
                response.failure(f"status {response.status_code}")
                return
            saw_done = False
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if line.startswith("event:") and "done" in line:
                    saw_done = True
            if saw_done:
                response.success()
            else:
                response.failure("stream closed without done event")
