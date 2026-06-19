from pathlib import Path

import fitz
import pytest

from app.services.pdf_extractor import (
    extract_and_persist,
    extract_text_from_pdf,
    load_extracted_text,
    save_extracted_text,
)


@pytest.fixture
def extracted_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "extracted"
    monkeypatch.setattr("app.core.config.EXTRACTED_DIR", target)
    return target


def _create_sample_pdf(path: Path, pages: list[str]) -> Path:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(path)
    document.close()
    return path


def test_extract_text_from_pdf_returns_page_content(tmp_path: Path) -> None:
    pdf_path = _create_sample_pdf(tmp_path / "sample.pdf", ["Hello page one", "Hello page two"])

    extracted = extract_text_from_pdf(pdf_path)

    assert extracted.page_count == 2
    assert extracted.pages[0].page_number == 1
    assert "Hello page one" in extracted.pages[0].text
    assert "Hello page two" in extracted.pages[1].text
    assert "Hello page one" in extracted.full_text
    assert "Hello page two" in extracted.full_text


def test_extract_text_from_pdf_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(tmp_path / "missing.pdf")


def test_extract_text_from_pdf_rejects_non_pdf(tmp_path: Path) -> None:
    text_path = tmp_path / "notes.txt"
    text_path.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ValueError, match="Only PDF files"):
        extract_text_from_pdf(text_path)


def test_save_and_load_extracted_text(
    tmp_path: Path,
    extracted_dir: Path,
) -> None:
    pdf_path = _create_sample_pdf(tmp_path / "persist.pdf", ["Persist me"])
    extracted = extract_text_from_pdf(pdf_path)

    json_path = save_extracted_text(extracted)

    assert json_path.parent == extracted_dir
    assert json_path.exists()

    loaded = load_extracted_text(pdf_path)
    assert loaded is not None
    assert loaded.page_count == 1
    assert loaded.full_text == extracted.full_text
    assert loaded.extracted_json_path == json_path


def test_extract_and_persist_writes_json(
    tmp_path: Path,
    extracted_dir: Path,
) -> None:
    pdf_path = _create_sample_pdf(tmp_path / "workflow.pdf", ["Workflow text"])

    extracted = extract_and_persist(pdf_path)

    assert extracted.extracted_json_path is not None
    assert extracted.extracted_json_path.exists()
    assert extracted.extracted_json_path.parent == extracted_dir
