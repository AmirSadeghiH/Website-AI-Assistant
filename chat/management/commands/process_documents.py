from django.core.management.base import BaseCommand, CommandError

from chat.document_pipeline import process_document


class Command(BaseCommand):
    help = "Process multiple knowledge documents sequentially."

    def add_arguments(self, parser):
        parser.add_argument("document_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        failures = []
        for document_id in options["document_ids"]:
            try:
                process_document(document_id)
            except Exception as exc:
                failures.append(f"{document_id}: {exc}")
        if failures:
            raise CommandError("; ".join(failures))
        self.stdout.write(self.style.SUCCESS("Document embedding completed."))
