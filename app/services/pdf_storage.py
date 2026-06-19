import re
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import ensure_upload_dir
from app.models.schemas import SavedPdf


def _safe_filename(name: str) -> str:
    path = Path(name)
    safe_stem = re.sub(r"[^\w\-]", "_", path.stem)[:100] or "document"
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{safe_stem}_{timestamp}.pdf"


def save_pdf(file_bytes: bytes, original_name: str) -> SavedPdf:
    if not original_name.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed.")

    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    upload_dir = ensure_upload_dir()
    saved_path = upload_dir / _safe_filename(original_name)
    saved_path.write_bytes(file_bytes)

    return SavedPdf(
        original_name=original_name,
        saved_path=saved_path,
        size_bytes=len(file_bytes),
    )


def list_saved_pdfs() -> list[SavedPdf]:
    upload_dir = ensure_upload_dir()
    pdfs: list[SavedPdf] = []

    for path in sorted(upload_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
        pdfs.append(
            SavedPdf(
                original_name=path.name,
                saved_path=path,
                size_bytes=path.stat().st_size,
            )
        )

    return pdfs
