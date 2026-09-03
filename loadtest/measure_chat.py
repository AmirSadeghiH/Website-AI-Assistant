import json
import time
import urllib.request


def req(path, payload=None):
    data = json.dumps(payload).encode() if payload else None
    r = urllib.request.Request(
        "http://127.0.0.1:8010" + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(r, timeout=180) as resp:
        body = resp.read()
    return resp.status, time.perf_counter() - t0, body


questions = [
    "شرایط دریافت وام چیه؟",
    "ساعات کاری مجموعه چیه؟",
    "چطور با پشتیبانی تماس بگیرم؟",
    "امکان همکاری تجاری وجود داره؟",
]
results = []
for i, q in enumerate(questions):
    s, dt, body = req("/api/chat/", {"message": q, "page_url": "https://x.example/"})
    d = json.loads(body.decode("utf-8"))
    lat = dt * 1000
    results.append(lat)
    print(
        "chat#%d status=%s latency=%.0fms fallback=%s citations=%d intent=%s"
        % (i + 1, s, lat, d.get("fallback"), len(d.get("citations", [])), d.get("intent"))
    )
results.sort()
print("p50=%.0fms max=%.0fms" % (results[len(results) // 2], results[-1]))
