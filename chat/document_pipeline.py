import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from defusedxml import ElementTree as DefusedElementTree
from filelock import FileLock, Timeout
import pymupdf
from django.conf import settings
from django.utils import timezone

from .models import Document


SUPPORTED_TYPES = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".text": "txt",
    ".docx": "docx",
}
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
# Zip-bomb / decompression guards for DOCX archives.
MAX_DOCX_PARTS = 2000
MAX_DOCX_UNCOMPRESSED_TOTAL = 64 * 1024 * 1024
MAX_DOCX_SINGLE_PART = 32 * 1024 * 1024


@contextmanager
def corpus_lock(timeout=30):
    data_dir = Path(settings.BASE_DIR) / "Data"
    lock = FileLock(str(data_dir / ".corpus.lock"), timeout=timeout)
    try:
        with lock:
            yield
    except Timeout as exc:
        raise RuntimeError("The knowledge corpus is busy. Try again shortly.") from exc


def detect_file_type(name):
    return SUPPORTED_TYPES.get(Path(name).suffix.lower())


def sniff_file_type(path):
    """Identify the real file type from content, not just the extension."""
    with path.open("rb") as handle:
        head = handle.read(64 * 1024)
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        return "docx"
    if b"\x00" in head:
        return None
    try:
        head.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    return "txt"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(text):
    text = re.sub(r"[•▪◦◆]+", " ", text or "")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def extract_pdf(path):
    pages = []
    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = clean_text(page.get_text())
            if text:
                pages.append({"page_number": page_number, "text": text})
    return pages


def extract_docx(path):
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_DOCX_PARTS:
            raise ValueError("فایل DOCX دارای بخش‌های داخلی بیش از حد مجاز است.")
        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > MAX_DOCX_UNCOMPRESSED_TOTAL:
            raise ValueError("حجم بازشده فایل DOCX بیش از حد مجاز است.")
        for info in infos:
            if info.file_size > MAX_DOCX_SINGLE_PART:
                raise ValueError(
                    "یکی از بخش‌های داخلی فایل DOCX بیش از حد بزرگ است."
                )
        xml = archive.read("word/document.xml")
    # defusedxml blocks entity-expansion (billion laughs) attacks.
    root = DefusedElementTree.fromstring(xml)
    paragraphs = []
    for paragraph in root.findall(".//w:p", namespace):
        text = "".join(
            node.text or ""
            for node in paragraph.findall(".//w:t", namespace)
        )
        if text.strip():
            paragraphs.append(text)
    text = clean_text("\n".join(paragraphs))
    return [{"page_number": 1, "text": text}] if text else []


def extract_document(path, file_type):
    if file_type == "pdf":
        return extract_pdf(path)
    if file_type == "docx":
        return extract_docx(path)
    if file_type == "txt":
        return [
            {"page_number": 1, "text": clean_text(path.read_text(encoding="utf-8-sig"))}
        ]
    raise ValueError("فرمت فایل پشتیبانی نمی‌شود. فقط PDF، TXT و DOCX مجاز هستند.")


def _read_artifacts():
    data_dir = Path(settings.BASE_DIR) / "Data"
    chunks_path = data_dir / "chunks.json"
    metadata_path = data_dir / "metadata.json"
    embeddings_path = data_dir / "embeddings.npy"
    chunks = json.loads(chunks_path.read_text(encoding="utf-8")) if chunks_path.exists() else []
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else []
    embeddings = np.load(embeddings_path).astype("float32") if embeddings_path.exists() else None
    return data_dir, chunks, metadata, embeddings


def _write_atomic(path, writer):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=path.suffix,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        writer(temporary_path)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def rebuild_document_embeddings(document):
    path = Path(document.file.path)
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError("حجم فایل نباید بیشتر از ۲۵ مگابایت باشد.")

    file_type = detect_file_type(path.name)
    if not file_type:
        raise ValueError("فرمت فایل پشتیبانی نمی‌شود. فقط PDF، TXT و DOCX مجاز هستند.")
    sniffed = sniff_file_type(path)
    if sniffed is None or sniffed != file_type:
        raise ValueError(
            "محتوای فایل با پسوند آن هم‌خوانی ندارد و پردازش نمی‌شود."
        )
    content_hash = sha256_file(path)
    if Document.objects.filter(
        content_hash=content_hash,
    ).exclude(pk=document.pk).exists():
        raise ValueError("این فایل قبلاً در پایگاه دانش پردازش شده است.")

    pages = extract_document(path, file_type)
    if not pages:
        raise ValueError("از فایل انتخاب‌شده متن قابل استفاده‌ای استخراج نشد.")

    document_key = f"uploaded-document-{document.pk}"
    from rag.build_embeddings import EmbeddingBuilder

    builder = EmbeddingBuilder()
    chunks, metadata = builder.chunk_doc(pages, document_key)
    if not chunks:
        raise ValueError("پس از chunk بندی، محتوای قابل embedding تولید نشد.")
    embeddings = builder.embed_chunks(chunks).astype("float32")

    with corpus_lock():
        data_dir, old_chunks, old_metadata, old_embeddings = _read_artifacts()
        if old_embeddings is not None and len(old_chunks) != len(old_embeddings):
            raise ValueError("فایل‌های corpus فعلی با یکدیگر هم‌خوانی ندارند.")

        keep_indexes = [
            index
            for index, item in enumerate(old_metadata)
            if item.get("doc_id") != document_key
        ]
        if old_embeddings is None:
            kept_embeddings = np.empty((0, embeddings.shape[1]), dtype="float32")
            kept_chunks = []
            kept_metadata = []
        else:
            kept_embeddings = old_embeddings[keep_indexes]
            kept_chunks = [old_chunks[index] for index in keep_indexes]
            kept_metadata = [old_metadata[index] for index in keep_indexes]

        for item in metadata:
            item["document_id"] = document.pk
            item["document_title"] = document.title
            item["source_type"] = file_type

        final_chunks = kept_chunks + chunks
        final_metadata = kept_metadata + metadata
        final_embeddings = np.vstack([kept_embeddings, embeddings])

        _write_atomic(
            data_dir / "chunks.json",
            lambda target: target.write_text(
                json.dumps(final_chunks, ensure_ascii=False),
                encoding="utf-8",
            ),
        )
        _write_atomic(
            data_dir / "metadata.json",
            lambda target: target.write_text(
                json.dumps(final_metadata, ensure_ascii=False),
                encoding="utf-8",
            ),
        )
        _write_atomic(
            data_dir / "embeddings.npy",
            lambda target: np.save(target, final_embeddings),
        )

    document.file_type = file_type
    document.content_hash = content_hash
    document.chunk_count = len(chunks)
    document.embedding_count = len(embeddings)
    document.status = "ready"
    document.error_message = ""
    document.processed_at = timezone.now()
    document.save(
        update_fields=(
            "file_type",
            "content_hash",
            "chunk_count",
            "embedding_count",
            "status",
            "error_message",
            "processed_at",
            "updated_at",
        ),
    )


def remove_document_embeddings(document_id):
    with corpus_lock():
        data_dir, old_chunks, old_metadata, old_embeddings = _read_artifacts()
        if old_embeddings is None:
            return
        if len(old_chunks) != len(old_metadata) or len(old_chunks) != len(old_embeddings):
            raise ValueError("فایل‌های corpus فعلی با یکدیگر هم‌خوانی ندارند.")

        document_key = f"uploaded-document-{document_id}"
        keep_indexes = [
            index
            for index, item in enumerate(old_metadata)
            if item.get("doc_id") != document_key
        ]
        if len(keep_indexes) == len(old_metadata):
            return

        _write_atomic(
            data_dir / "chunks.json",
            lambda target: target.write_text(
                json.dumps(
                    [old_chunks[index] for index in keep_indexes],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            ),
        )
        _write_atomic(
            data_dir / "metadata.json",
            lambda target: target.write_text(
                json.dumps(
                    [old_metadata[index] for index in keep_indexes],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            ),
        )
        _write_atomic(
            data_dir / "embeddings.npy",
            lambda target: np.save(target, old_embeddings[keep_indexes]),
        )


def process_document(document_id):
    document = Document.objects.get(pk=document_id)
    document.status = "processing"
    document.error_message = ""
    document.save(update_fields=("status", "error_message", "updated_at"))
    try:
        rebuild_document_embeddings(document)
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)[:4000]
        document.save(update_fields=("status", "error_message", "updated_at"))
        raise


def enqueue_documents(document_ids):
    documents = Document.objects.filter(pk__in=document_ids).exclude(
        status__in=("queued", "processing"),
    )
    ids = list(documents.values_list("pk", flat=True))
    if not ids:
        return 0
    documents.update(status="queued", error_message="", updated_at=timezone.now())

    command = [
        sys.executable,
        str(Path(settings.BASE_DIR) / "manage.py"),
        "process_documents",
        *[str(document_id) for document_id in ids],
    ]
    log_path = Path(settings.BASE_DIR) / "embedding_jobs.log"
    log_handle = log_path.open("a", encoding="utf-8")
    kwargs = {
        "cwd": settings.BASE_DIR,
        "stdin": subprocess.DEVNULL,
        "stdout": log_handle,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen(command, **kwargs)
    finally:
        log_handle.close()
    return len(ids)


def enqueue_document(document_id):
    return enqueue_documents([document_id])
