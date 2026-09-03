"""Continuous background worker (deployment service).

Polls queued work so platforms like Railway can run a dedicated worker
service without cron:

    python manage.py runworker --loop

Processes, in order: crawl jobs → queued documents. With ``--loop`` it
sleeps between polls; a single pass runs otherwise.
"""

import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from chat.crawler import run_crawl_job
from chat.document_pipeline import process_documents_queued


class Command(BaseCommand):
    help = "Background worker: processes queued crawl jobs and documents."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true")
        parser.add_argument("--interval", type=int, default=5)

    def handle(self, *args, **options):
        loop = options["loop"]
        interval = max(1, options["interval"])
        while True:
            try:
                close_old_connections()
                self._run_once()
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"Worker error: {exc}")
            if not loop:
                return
            time.sleep(interval)

    def _run_once(self):
        from chat.models import CrawlJob, Document

        pending_jobs = CrawlJob.objects.filter(status="queued").values_list(
            "pk", flat=True
        )
        for job_id in list(pending_jobs):
            self.stdout.write(f"Crawl job {job_id} → running")
            run_crawl_job(
                job_id, log=lambda message: self.stdout.write(message)
            )

        pending_docs = Document.objects.filter(status="queued").values_list(
            "pk", flat=True
        )
        for document_id in list(pending_docs):
            self.stdout.write(f"Document {document_id} → processing")
            try:
                process_documents_queued([document_id])
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(f"Document {document_id} failed: {exc}")
