import os
import sys

sys.path.insert(0, r"D:\ai-support-platform")
os.chdir(r"D:\ai-support-platform")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DEBUG", "True")

import django

django.setup()

from chat.crawler import _extract_text, _extract_links

html = """
<html><head><title>فروشگاه نمونه</title><style>.x{color:red}</style></head>
<body>
<nav>منوی اصلی</nav>
<h1>شرایط مرجوعی</h1>
<p>تا ۷ روز پس از خرید می‌توانید محصول را مرجوع کنید.</p>
<a href="/about">درباره ما</a>
<a href="https://google.com/x">بیرونی</a>
<script>alert(1)</script>
<!-- hidden comment -->
<footer>کپی‌رایت</footer>
</body></html>
"""

title, text = _extract_text(html)
print("TITLE:", title)
print("TEXT:", text[:200])
print("LINKS:", _extract_links(html, "https://example.com/page"))

# SSRF guard checks
from chat.crawler import resolve_public_host, CrawlBlockedError

for bad in ("http://127.0.0.1:8000/x", "http://192.168.1.10/admin", "file:///etc/passwd", "http://user:pass@169.254.169.254/latest"):
    try:
        resolve_public_host(bad)
        print("NOT BLOCKED (BAD):", bad)
    except CrawlBlockedError as exc:
        print("BLOCKED:", bad, "->", str(exc)[:60])
