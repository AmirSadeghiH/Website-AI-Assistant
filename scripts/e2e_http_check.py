"""End-to-end HTTP flow test against the running dev server (port 8010).

Verifies the complete product contract over real HTTP:
  1. /api/widget-config/  — new v4 keys present
  2. /demo/               — page serves + widget.js reference
  3. widget.js            — v4 markers (stream, leadform, handoff, preview)
  4. /api/chat/           — real RAG answer + conversation + token
  5. /api/history/        — HMAC token grants transcript
  6. /api/leads/          — honeypot + real lead
  7. /api/handoff/        — handoff request + channels response
  8. /panel/preview/      — live preview page serves (staff only → login redirect)
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8010"
PASS = []
FAIL = []


def check(name, condition, detail=""):
    (PASS if condition else FAIL).append((name, detail))
    print(("OK  " if condition else "FAIL") + " " + name + ("  " + detail if detail else ""))


def req(path, payload=None, method=None, headers=None):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# 1. widget-config carries the v4 keys
status, body = req("/api/widget-config/")
cfg = json.loads(body.decode("utf-8"))
check("widget-config 200", status == 200)
for key in ("enable_streaming", "show_citations", "enable_lead_capture",
            "enable_handoff", "handoff_trigger", "handoff_urls"):
    check("config has %s" % key, key in cfg, str(cfg.get(key, ""))[:60])

# 2. demo page serves and references widget.js
status, body = req("/static/demo.html")
check("demo page 200", status == 200)
check("demo references widget.js", b"widget.js" in body)

# 3. widget.js serves with v4 markers
status, body = req("/static/widget/widget.js")
js = body.decode("utf-8", "replace")
check("widget.js 200", status == 200)
for marker in ("streamChat", "buildLeadForm", "maybeShowHandoff", "bindPreviewChannel",
               "restoreHistory", "buildCitations", "asw-leadform", "asw-citations",
               "AI Support Widget v4"):
    check("widget.js has %s" % marker, marker in js)

# 4. real chat with RAG
status, body = req("/api/chat/", {"message": "ساعات کاری مجموعه چیه؟",
                                  "page_url": "https://e2e.example/"})
check("chat 200", status == 200, "status=%s" % status)
data = json.loads(body.decode("utf-8"))
conv_id = data.get("conversation_id", "")
conv_token = data.get("conversation_token", "")
check("chat has answer", bool(data.get("answer")), data.get("answer", "")[:60])
check("chat has conversation_id", bool(conv_id))
check("chat has conversation_token", bool(conv_token))
check("chat has citations list", isinstance(data.get("citations"), list))
check("chat has intent", bool(data.get("intent")), str(data.get("intent")))
check("chat has latency_ms", "latency_ms" in data)

# 5. history with HMAC token
status, body = req(
    "/api/history/?conversation_id=%s" % conv_id,
    headers={"X-Conversation-Token": conv_token},
)
check("history 200 with token", status == 200)
hist = json.loads(body.decode("utf-8"))
check("history has messages", len(hist.get("messages", [])) >= 2,
      "%d messages" % len(hist.get("messages", [])))

status, body = req("/api/history/?conversation_id=%s" % conv_id)
check("history 403 without token", status == 403, "status=%s" % status)

# 6. leads: honeypot then real
status, body = req("/api/leads/", {
    "name": "بات آزمایشی", "email": "bot@spam.example",
    "website": "http://spam.example",
})
check("lead honeypot fake-success", status == 200)
status, body = req("/api/leads/", {
    "name": "کاربر واقعی", "email": "real@example.com",
    "phone": "09120000000",
    "note": "درخواست دمو",
    "conversation_id": conv_id,
    "conversation_token": conv_token,
})
check("lead created 201", status == 201, "status=%s" % status)
check("lead Persian message", "ثبت شد" in body.decode("utf-8"))

# 7. handoff
status, body = req("/api/handoff/", {
    "channel": "telegram",
    "message": "می‌خوام با کارشناس حرف بزنم",
    "conversation_id": conv_id,
    "conversation_token": conv_token,
})
check("handoff 201", status == 201)
hd = json.loads(body.decode("utf-8"))
check("handoff returns channels", "channels" in hd, json.dumps(hd.get("channels", {}))[:60])
check("handoff returns support_email", "support_email" in hd)

# 8. conversation now handed_off
status, body = req(
    "/api/history/?conversation_id=%s" % conv_id,
    headers={"X-Conversation-Token": conv_token},
)
# (status check of conversation object via history still works)
check("history still accessible after handoff", status == 200)

# 9. preview page requires staff (urllib follows redirects, so use a
#    no-redirect opener to see the raw 302)
import http.client

conn = http.client.HTTPConnection("127.0.0.1", 8010, timeout=30)
conn.request("GET", "/panel/preview/")
raw_status = conn.getresponse().status
conn.close()
check("panel preview redirects anon", raw_status in (301, 302), "raw status=%s" % raw_status)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    for name, detail in FAIL:
        print("  FAILED:", name, detail)
    raise SystemExit(1)
print("E2E HTTP FLOW: ALL OK")
