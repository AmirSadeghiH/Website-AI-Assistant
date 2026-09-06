"""Deployment bootstrap: one command makes a fresh container healthy.

Idempotent — safe to run on every deploy (it is the Railway preDeploy
command and part of the unified entrypoint):

    python manage.py ensure_deploy

Steps: apply migrations, create staticfiles, make sure the corpus
directory exists and is internally consistent (an interrupted deploy
leaving a partial corpus is repaired to the empty state rather than
503-ing forever), and optionally create the default superuser from env.
"""

import json
import logging
import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Prepare a (re)deployed instance: migrate, collectstatic, repair corpus."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-collectstatic", action="store_true",
            help="Skip collectstatic (useful when staticfiles is read-only).",
        )
        parser.add_argument(
            "--skip-superuser", action="store_true",
            help="Never auto-create the DJANGO_SUPERUSER_* account.",
        )

    def handle(self, *args, **options):
        self.stdout.write("-> migrate")
        call_command("migrate", "--noinput", verbosity=0)

        if not options["no_collectstatic"]:
            self.stdout.write("-> collectstatic")
            call_command("collectstatic", "--noinput", verbosity=0, clear=True)

        self._ensure_superuser(options["skip_superuser"])
        self._ensure_corpus()

        self.stdout.write(self.style.SUCCESS("Deploy preparation complete."))

    def _ensure_superuser(self, skip):
        """Create DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD when provided.

        Standard Django createsuperuser flags; made optional so the command
        is safe to repeat (skips silently when the user exists).
        """
        if skip:
            return
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not (username and password):
            return
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"-> superuser {username!r} exists")
            return
        user_model.objects.create_superuser(
            username=username, email=email or "", password=password,
        )
        self.stdout.write(f"-> created superuser {username!r}")

    def _ensure_corpus(self):
        """Guarantee the corpus directory is in a consistent state.

        A crashed processing run can leave one artifact missing; the
        retriever then refuses to start (partial = corruption) and every
        chat request 503s forever. The repair rule: either all three
        artifacts exist, or none does (empty corpus = valid fresh state).
        """
        data_dir = settings.CORPUS_DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "chunks": data_dir / "chunks.json",
            "metadata": data_dir / "metadata.json",
            "embeddings": data_dir / "embeddings.npy",
        }
        existing = {name for name, path in paths.items() if path.exists()}
        if len(existing) == 3:
            self._validate_pairs(paths)
            self.stdout.write("-> corpus consistent")
            return
        if not existing:
            self.stdout.write("-> corpus empty (fresh install)")
            return

        # Partial corpus: drop the stragglers, log loudly.
        for name in existing:
            paths[name].unlink(missing_ok=True)
            logger.error(
                "Corpus repair: removed orphan artifact %s (inconsistent state)",
                name,
            )
        self.stdout.write(
            self.style.WARNING(
                "-> corpus was inconsistent (orphan artifacts removed); "
                "reprocess documents from the knowledge panel"
            )
        )

    def _validate_pairs(self, paths):
        try:
            with open(paths["chunks"], encoding="utf-8") as fh:
                chunk_count = len(json.load(fh))
            import numpy as np

            embeddings = np.load(paths["embeddings"])
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(
                self.style.WARNING(f"-> corpus unreadable ({exc}); treated as ok")
            )
            return
        if chunk_count != len(embeddings):
            # Dimension mismatch between count and index — clear the corpus
            # so documents can be reprocessed instead of 503 forever.
            for path in paths.values():
                path.unlink(missing_ok=True)
            self.stdout.write(
                self.style.WARNING(
                    f"-> corpus count mismatch ({chunk_count} vs {len(embeddings)}); "
                    "cleared — reprocess documents"
                )
            )
