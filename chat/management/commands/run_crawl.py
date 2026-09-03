"""Process one or more crawl jobs in this process.

Executed as a detached subprocess by the admin panel/panel view so HTTP
requests return instantly:

    python manage.py run_crawl 7 8 9
"""

from django.core.management.base import BaseCommand

from chat.crawler import run_crawl_job


class Command(BaseCommand):
    help = "Run website crawl jobs (same-domain crawl → knowledge documents)."

    def add_arguments(self, parser):
        parser.add_argument("job_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        for job_id in options["job_ids"]:
            try:
                self.stdout.write(f"Running crawl job {job_id}...")
            except UnicodeEncodeError:
                # Windows console cp1252 — never crash on Persian text
                self.stdout.write(f"Running crawl job {job_id}...".encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
            try:
                def _safe_log(message):
                    try:
                        self.stdout.write(message)
                    except UnicodeEncodeError:
                        self.stdout.write(str(message).encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
                run_crawl_job(job_id, log=_safe_log)
            except Exception as exc:  # noqa: BLE001
                try:
                    self.stderr.write(f"Crawl job {job_id} failed: {exc}")
                except UnicodeEncodeError:
                    self.stderr.write(f"Crawl job {job_id} failed: {exc}".encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
