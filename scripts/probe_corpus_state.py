"""Inspect the tracked corpus files (chunks/metadata) + dev DB documents."""
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()


def git_show(path):
    out = subprocess.run(
        ["git", "show", f"HEAD:{path}"], capture_output=True, check=True
    )
    return out.stdout.decode("utf-8")


chunks = json.loads(git_show("Data/chunks.json"))
metadata = json.loads(git_show("Data/metadata.json"))
print(f"HEAD chunks:    {len(chunks)}")
print(f"HEAD metadata:  {len(metadata)}")
if chunks:
    print("chunk[0][:120]:", chunks[0][:120].replace("\n", " "))
doc_ids = {m.get("document_id") for m in metadata}
print("doc ids in metadata:", sorted(str(x) for x in doc_ids))

from chat.models import Document  # noqa: E402

docs = list(Document.objects.all().order_by("pk"))
print(f"\nDB documents: {len(docs)}")
for d in docs:
    print(
        f"  #{d.pk} [{d.status}] chunks={d.chunk_count} "
        f"embeddings={d.embedding_count} title={d.title[:40]!r}"
    )
