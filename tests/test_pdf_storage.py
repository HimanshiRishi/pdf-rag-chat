from pathlib import Path

import pytest

from app.services.pdf_storage import list_saved_pdfs, save_pdf


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "uploads"
    monkeypatch.setattr("app.core.config.UPLOAD_DIR", target)
    return target


def test_save_pdf_writes_file_to_upload_dir(upload_dir: Path) -> None:
    content = b"%PDF-1.4 test content"

    saved = save_pdf(content, "sample report.pdf")

    assert saved.saved_path.parent == upload_dir
    assert saved.saved_path.exists()
    assert saved.saved_path.read_bytes() == content
    assert saved.original_name == "sample report.pdf"
    assert saved.size_bytes == len(content)
    assert saved.saved_path.suffix == ".pdf"


def test_save_pdf_rejects_non_pdf(upload_dir: Path) -> None:
    with pytest.raises(ValueError, match="Only PDF files"):
        save_pdf(b"hello", "notes.txt")


def test_save_pdf_rejects_empty_file(upload_dir: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        save_pdf(b"", "empty.pdf")


def test_list_saved_pdfs_returns_saved_files(upload_dir: Path) -> None:
    save_pdf(b"%PDF-1.4 one", "first.pdf")
    save_pdf(b"%PDF-1.4 two", "second.pdf")

    saved = list_saved_pdfs()

    assert len(saved) == 2
    assert all(path.saved_path.parent == upload_dir for path in saved)
