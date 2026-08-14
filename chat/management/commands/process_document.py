from django.core.management.base import BaseCommand, CommandError

from chat.document_pipeline import process_document


class Command(BaseCommand):
    help = "Extract a knowledge document, chunk it, embed it and update the local corpus."

    def add_arguments(self, parser):
        parser.add_argument("document_id", type=int)

    def handle(self, *args, **options):
        try:
            process_document(options["document_id"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Document embedding completed."))
