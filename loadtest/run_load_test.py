"""Stdlib load test — ramps 10→50→100→200 virtual users.

No locust dependency (the sandbox can't pip-install); pure
threading + urllib. Measures:
  Phase A (light):  /api/health/, /api/widget-config/, /api/events/
  Phase B (heavy):  /api/chat/ real RAG answers, small sample
Outputs p50/p95 latency + throughput + error counts per phase.
"""
import json
import random
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict

BASE = "http://127.0.0.1:8010"
QUESTIONS = [
    "شرایط دریافت وام چیه؟",
    "ساعات کاری مجموعه چیه؟",
    "چطور با پشتیبانی تماس بگیرم؟",
    "امکان همکاری تجاری وجود داره؟",
]
EVENTS = ("widget_opened", "faq_clicked", "suggestion_clicked")

_user_ctx = threading.local()


def _request(path, payload=None, timeout=90):
    url = BASE + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, body, time.perf_counter() - start
    except urllib.error.HTTPError as exc:
        try:
            exc.read()
        except Exception:
            pass
        return exc.code, b"", time.perf_counter() - start


class Phase:
    def __init__(self, name, duration, workers, fn):
        self.name = name
        self.duration = duration
        self.workers = workers
        self.fn = fn
        self.latencies = defaultdict(list)  # key -> [seconds]
        self.statuses = defaultdict(int)    # key -> count
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def _worker(self):
        while not self.stop.is_set():
            key, status, elapsed = self.fn()
            with self.lock:
                self.latencies[key].append(elapsed)
                self.statuses[(key, status)] += 1

    def run(self):
        threads = [threading.Thread(target=self._worker, daemon=True) for _ in range(self.workers)]
        started = time.perf_counter()
        for thread in threads:
            thread.start()
        time.sleep(self.duration)
        self.stop.set()
        for thread in threads:
            thread.join(timeout=30)
        wall = time.perf_counter() - started
        return wall

    def report(self, wall):
        total_reqs = sum(self.statuses.values())
        print(f"\n── {self.name}: {self.workers} vusers · {self.duration}s ──")
        print(f"   requests: {total_reqs}  ·  throughput: {total_reqs / wall:.1f} rps")
        for key, lat in sorted(self.latencies.items()):
            lat_ms = sorted(x * 1000 for x in lat)
            p50 = lat_ms[len(lat_ms) // 2]
            p95 = lat_ms[min(len(lat_ms) - 1, int(len(lat_ms) * 0.95))]
            err = sum(count for (k, s), count in self.statuses.items() if k == key and s >= 400)
            err_non_429 = sum(
                count for (k, s), count in self.statuses.items() if k == key and s >= 400 and s != 429
            )
            print(
                f"   {key:<28} n={len(lat_ms):>5}  p50={p50:7.0f}ms  p95={p95:7.0f}ms"
                f"  errors(≠429)={err_non_429}"
            )


def fn_health():
    status, _, elapsed = _request("/api/health/")
    return "[light] health", status, elapsed


def fn_config():
    status, _, elapsed = _request("/api/widget-config/")
    return "[light] widget-config", status, elapsed


def fn_events():
    event = random.choice(EVENTS)
    status, _, elapsed = _request(
        "/api/events/", {"event_type": event, "metadata": {"loadtest": True}}
    )
    return "[light] events", status, elapsed


def fn_chat():
    if not hasattr(_user_ctx, "conv"):
        _user_ctx.conv = ""
    payload = {"message": random.choice(QUESTIONS), "page_url": "https://loadtest.example/x"}
    if _user_ctx.conv:
        payload["conversation_id"] = _user_ctx.conv
    status, body, elapsed = _request("/api/chat/", payload)
    if status == 200:
        try:
            _user_ctx.conv = json.loads(body.decode("utf-8")).get("conversation_id", "")
        except Exception:
            pass
    return "[heavy] chat (RAG)", status, elapsed


def main():
    print(f"Load test against {BASE}")
    for name, workers, duration, fns in (
        ("Ramp A1", 10, 12, (fn_health, fn_config, fn_events)),
        ("Ramp A2", 50, 12, (fn_health, fn_config, fn_events)),
        ("Ramp A3", 100, 12, (fn_health, fn_config, fn_events)),
        ("Ramp A4", 200, 12, (fn_health, fn_config, fn_events)),
    ):
        phase = Phase(name, duration, workers, lambda: random.choice(fns)())
        wall = phase.run()
        phase.report(wall)
        time.sleep(2)

    # Heavy: real RAG chat, modest sample (cost-bounded)
    phase = Phase("Ramp B", 40, 4, fn_chat)
    wall = phase.run()
    phase.report(wall)
    print("\nDONE")


if __name__ == "__main__":
    main()
