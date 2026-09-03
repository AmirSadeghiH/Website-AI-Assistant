"""Render /panel/customizer/ with the test client, extract every inline
<script> block, and syntax-check each with node. Catches template/JS bugs
that break tab switching and the live preview."""
import os
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings

settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]

from django.contrib.auth.models import User
from django.test import Client

user, _ = User.objects.get_or_create(username="panel_smoke", is_staff=True)
client = Client()
client.force_login(user)

resp = client.get("/panel/customizer/")
html = resp.content.decode("utf-8")
print("customizer status:", resp.status_code)

scripts = re.findall(r"<script(?![^>]*src)[^>]*>(.*?)</script>", html, re.DOTALL)
print("inline script blocks:", len(scripts))

ok = True
for i, code in enumerate(scripts):
    if not code.strip():
        continue
    proc = subprocess.run(
        ["node", "--check", "/dev/stdin"] if False else ["node", "-e", "new (require('vm').Script)(process.argv[1])", code],
        capture_output=True,
        text=True,
    )
    status = "OK " if proc.returncode == 0 else "BAD"
    if proc.returncode != 0:
        ok = False
        print(f"[{status}] block {i}:")
        print(proc.stderr[:1500])
    else:
        print(f"[{status}] block {i} ({len(code)} chars)")

# Check tab wiring present in rendered HTML
for marker in ('data-tab="identity"', 'data-pane="identity"',
               'data-tab="appearance"', 'data-pane="appearance"',
               'data-tab="position"', 'data-pane="position"',
               'data-tab="behavior"', 'data-pane="behavior"',
               'data-tab="lead"', 'data-pane="lead"',
               'id="preview-frame"', 'aiss:config', 'preview_payload'):
    found = marker in html
    if not found:
        ok = False
    print(("OK  " if found else "MISS") + " rendered: " + marker)

# Check preview iframe src and that X-Frame-Options won't deny
resp2 = client.get("/panel/preview/")
print("preview page status:", resp2.status_code)
print("X-Frame-Options:", resp2.headers.get("X-Frame-Options", "(none)"))
if resp2.status_code != 200:
    ok = False

# Ensure preview page embeds the widget script with data-preview
pv = resp2.content.decode("utf-8")
check_preview_widget = 'data-preview="1"' in pv and "widget.js" in pv
print(("OK  " if check_preview_widget else "MISS") + " preview embeds widget.js with data-preview")
if not check_preview_widget:
    ok = False

print("CUSTOMIZER RENDER: " + ("ALL OK" if ok else "PROBLEMS FOUND"))
sys.exit(0 if ok else 1)
