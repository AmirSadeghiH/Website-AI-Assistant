"""Website crawler (feature #5) with hard SSRF protections.

Security model — the crawler is triggered by an authenticated admin but
crawls *external* content, so it must never become a pivot into internal
networks:

1. Scheme allowlist: http/https only, no userinfo in the URL.
2. DNS-based SSRF guard: every host (including each redirect hop) must
   resolve exclusively to public, globally-routable IPs.
3. Manual redirect handling — auto-redirect is disabled so every hop is
   re-validated.
4. Same-domain policy: the crawler never leaves the start host.
5. robots.txt is fetched and honoured (per-host, cached in the job).
6. Bounded work: max pages, per-page timeout, max bytes, inter-request delay.

Extraction strips scripts/styles/comments and keeps readable text; each
page becomes a ``Document`` (source_type=crawl) queued for embedding.
"""

import ipaddress
import socket
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib import robotparser

import httpx

from django.conf import settings
from django.utils import timezone

from .document_pipeline import clean_text
from .models import CrawlJob, Document

USER_AGENT = "AI-Support-Crawler/1.0 (+support widget knowledge indexer)"
DEFAULT_MAX_PAGES = 30
MAX_PAGE_BYTES = 3 * 1024 * 1024
REQUEST_TIMEOUT = 15.0
REQUEST_DELAY = 0.6
MAX_REDIRECTS = 4

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".css", ".js",
    ".pdf", ".zip", ".rar", ".7z", ".mp3", ".mp4", ".avi", ".mov", ".woff",
    ".woff2", ".ttf", ".eot", ".xlsx", ".doc", ".docx", ".ppt", ".pptx",
    ".xml", ".rss", ".json",
)


class CrawlBlockedError(Exception):
    """A URL is not safe or not permitted to crawl."""


def _is_public_ip(ip):
    parsed = ipaddress.ip_address(ip)
    return (
        parsed.is_global
        and not parsed.is_loopback
        and not parsed.is_private
        and not parsed.is_link_local
        and not parsed.is_multicast
        and not parsed.is_reserved
        and not parsed.is_unspecified
    )


def resolve_public_host(url):
    """Return the hostname of ``url`` if it resolves to public IPs only.

    Raises CrawlBlockedError for private/loopback/link-local targets —
    this is the core SSRF guard for the crawler.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise CrawlBlockedError("فقط http و https مجاز است.")
    if parts.username or parts.password:
        raise CrawlBlockedError("URL نباید شامل نام کاربری/رمز باشد.")
    hostname = parts.hostname
    if not hostname:
        raise CrawlBlockedError("URL فاقد hostname است.")
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise CrawlBlockedError(f"دامنه قابل حل نیست: {hostname}") from exc
    addresses = {info[4][0] for info in infos}
    for address in addresses:
        if not _is_public_ip(address):
            raise CrawlBlockedError(
                f"دامنه به آدرس غیرعمومی ({address}) اشاره می‌کند و اجازه‌ی "
                "کرال ندارد."
            )
    return hostname


def normalize_url(url, base=None):
    """Canonicalize a URL; drops fragments, keeps scheme/host/path/query."""
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https"):
        raise CrawlBlockedError("فقط http و https مجاز است.")
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


DROP_TAGS = {
    "script", "style", "noscript", "template", "svg", "iframe", "form",
    "header", "footer", "nav", "aside", "button", "select", "option",
}


class _ReadableTextParser(HTMLParser):
    """Stdlib HTML → readable text (no external dependency).

    Tracks dropped containers (script/style/nav/...) and HTML comments so
    only real page content survives. Block-level tags insert newlines to
    keep sentence boundaries intact.
    """

    BLOCK_TAGS = {
        "p", "div", "section", "article", "li", "ul", "ol", "tr", "table",
        "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "blockquote", "pre",
        "td", "th", "main", "dl", "dt", "dd",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.drop_depth = 0
        self.parts = []
        self.title_parts = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if self.drop_depth:
            if tag not in ("br", "hr", "img", "input", "meta", "link"):
                self.drop_depth += 1
            return
        if tag in DROP_TAGS:
            self.drop_depth = 1
            return
        if tag == "title":
            self.in_title = True
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag in self.BLOCK_TAGS and not self.drop_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.drop_depth:
            self.drop_depth -= 1
            return
        if tag == "title":
            self.in_title = False
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_comment(self, data):
        pass  # comments are dropped

    def handle_data(self, data):
        if self.drop_depth:
            return
        if self.in_title:
            self.title_parts.append(data)
        else:
            self.parts.append(data)


def _extract_text(html):
    """Readable text extraction: drop scripts/styles/comments/chrome."""
    parser = _ReadableTextParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return "", clean_text(html)
    title = clean_text(" ".join(parser.title_parts))[:200]
    text = clean_text("".join(parser.parts))
    return title, text


def _extract_links(html, base_url):
    parser = _LinkParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return []
    links = []
    for href in parser.hrefs:
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        try:
            absolute = normalize_url(href, base=base_url)
        except CrawlBlockedError:
            continue
        links.append(absolute)
    return links


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.hrefs.append(value)


class _RobotCache:
    """Per-host robots.txt cache honouring crawl rules."""

    def __init__(self, client):
        self._client = client
        self._cache = {}

    def allowed(self, url):
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        parser = self._cache.get(origin)
        if parser is None:
            parser = robotparser.RobotFileParser()
            parser.url = f"{origin}/robots.txt"
            try:
                response = self._client.get(parser.url)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    # Unreachable/absent robots.txt → permissive.
                    parser.allow_all = True
            except httpx.HTTPError:
                parser.allow_all = True
            self._cache[origin] = parser
        return parser.can_fetch(USER_AGENT, url)


def crawl_page(client, url):
    """Fetch one page (following redirects manually with SSRF re-checks).

    Returns (final_url, html) or raises CrawlBlockedError/httpx errors.
    """
    current = url
    for _hop in range(MAX_REDIRECTS + 1):
        resolve_public_host(current)
        response = client.get(current, follow_redirects=False)
        is_redirect = getattr(response, "is_redirect", False)
        # httpx <0.28 had is_permanent_redirect; 0.28+ removed it. Fall back to status check.
        if not is_redirect:
            try:
                is_redirect = bool(response.is_redirect)
            except Exception:
                is_redirect = response.status_code in (301, 302, 303, 307, 308)
        if is_redirect:
            location = response.headers.get("location", "")
            if not location:
                break
            current = normalize_url(location, base=str(response.url))
            continue
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code}",
                request=response.request,
                response=response,
            )
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise CrawlBlockedError(f"نوع محتوا پشتیبانی نمی‌شود: {content_type[:60]}")
        content = response.content[:MAX_PAGE_BYTES]
        return str(response.url), content.decode(response.encoding or "utf-8", errors="replace")
    raise CrawlBlockedError("تعداد بازگردانی‌های redirect بیش از حد مجاز است.")


def _same_host(url, start_host):
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    start = start_host.lower().rstrip(".")
    return host == start or host == f"www.{start}" or start == f"www.{host}"


def run_crawl_job(job_id, log=lambda message: None):
    """Execute a CrawlJob: BFS same-domain crawl → Documents → embeddings.

    Designed to run inside the ``run_crawl`` management command process —
    failures on individual pages are logged and never abort the job.
    """
    job = CrawlJob.objects.get(pk=job_id)
    if job.status == "running":
        return
    job.status = "running"
    job.error_message = ""
    job.save(update_fields=("status", "error_message", "updated_at"))

    logs = []

    def _log(message):
        logs.append(f"[{timezone.now():%H:%M:%S}] {message}")
        log(message)

    def _flush_logs():
        CrawlJob.objects.filter(pk=job.pk).update(log="\n".join(logs[-200:]))

    try:
        start_host = resolve_public_host(job.start_url)
        start_url = normalize_url(job.start_url)
        _log(f"شروع کرال: {start_url} (سقف {job.max_pages} صفحه)")

        with httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=False,
            trust_env=False,
            limits=httpx.Limits(max_connections=4),
        ) as client:
            robots = _RobotCache(client)
            queue = [start_url]
            seen = {start_url}
            processed = 0

            while queue and processed < job.max_pages:
                url = queue.pop(0)
                if not _same_host(url, start_host):
                    continue
                if not robots.allowed(url):
                    _log(f"رد شد (robots.txt): {url}")
                    continue
                try:
                    final_url, html = crawl_page(client, url)
                except (CrawlBlockedError, httpx.HTTPError) as exc:
                    _log(f"خطا در {url}: {str(exc)[:120]}")
                    job.pages_failed += 1
                    continue

                title, text = _extract_text(html)
                for link in _extract_links(html, final_url):
                    if not _same_host(link, start_host):
                        continue
                    if any(link.lower().split("?")[0].endswith(ext) for ext in SKIP_EXTENSIONS):
                        continue
                    normalized = link.split("#")[0]
                    if normalized not in seen:
                        seen.add(normalized)
                        queue.append(normalized)

                if len(text) < 120:
                    _log(f"رد شد (متن کوتاه): {final_url}")
                    continue
                if any(final_url.lower().split("?")[0].endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue

                _index_page(final_url, title, text, job, _log)
                processed += 1
                job.pages_found = processed
                time.sleep(REQUEST_DELAY)

            job.status = "done"
            _log(f"کرال کامل شد: {processed} صفحه پردازش شد.")

    except Exception as exc:  # noqa: BLE001 — job-level failure isolation
        job.status = "failed"
        job.error_message = str(exc)[:2000]
        _log(f"خطای کلی کرال: {str(exc)[:200]}")
    finally:
        CrawlJob.objects.filter(pk=job.pk).update(
            status=job.status,
            pages_found=job.pages_found,
            pages_indexed=job.pages_indexed,
            pages_failed=job.pages_failed,
            error_message=job.error_message,
            log="\n".join(logs[-200:]),
            updated_at=timezone.now(),
        )


def _index_page(url, title, text, job, log):
    """Create/refresh the Document for one crawled page."""
    import hashlib

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing_by_url = Document.objects.filter(source_url=url).first()
    if existing_by_url is not None:
        if existing_by_url.content_hash == content_hash:
            log(f"بدون تغییر: {url}")
            return
        document = existing_by_url
        document.source_text = text
        document.status = "queued"
        document.error_message = ""
    elif Document.objects.filter(content_hash=content_hash).exists():
        log(f"محتوای تکراری: {url}")
        return
    else:
        document = Document(
            title=title or url[:200],
            source_type="crawl",
            source_url=url,
            source_text=text,
            status="queued",
        )

    document.title = title or document.title or url[:200]
    document.save()

    from .document_pipeline import process_document

    try:
        process_document(document.pk)
        job.pages_indexed += 1
        log(f"ایندکس شد: {url}")
    except Exception as exc:
        job.pages_failed += 1
        log(f"خطای ایندکس {url}: {str(exc)[:120]}")


def enqueue_crawl_job(job_id):
    """Spawn the detached run_crawl process for one job (mirrors the
    document pipeline's queue pattern).

    On Windows the child inherits the console code page (cp1252) by
    default, so Persian log lines must be forced to UTF-8 or the very
    first _log() call crashes with charmap/\\u06cc and the job fails
    instantly — that is the bug reported in the log excerpt.
    """
    from .document_pipeline import should_spawn_inline_worker

    if not should_spawn_inline_worker():
        # Container mode: the runworker --loop process handles the queue.
        return
    import os
    import subprocess
    import sys
    from pathlib import Path

    from django.conf import settings as _settings

    command = [
        sys.executable,
        str(Path(_settings.BASE_DIR) / "manage.py"),
        "run_crawl",
        str(job_id),
    ]
    log_path = Path(_settings.BASE_DIR) / "embedding_jobs.log"
    log_handle = log_path.open("a", encoding="utf-8")
    # Force UTF-8 for the child so Persian output never hits cp1252.
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    kwargs = {
        "cwd": _settings.BASE_DIR,
        "stdin": subprocess.DEVNULL,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
        "env": env,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(command, **kwargs)
    finally:
        log_handle.close()
