from pathlib import Path

import pytest

from app.models.schemas import ExtractedPage, ExtractedPdf
from app.rag.chunker import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    chunk_and_persist,
    chunk_extracted_pdf,
    load_chunks,
    save_chunks,
    split_text_into_chunks,
)


@pytest.fixture
def chunks_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "chunks"
    monkeypatch.setattr("app.core.config.CHUNKS_DIR", target)
    return target


def _extracted_pdf(tmp_path: Path, pages: list[str]) -> ExtractedPdf:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    return ExtractedPdf(
        source_path=pdf_path,
        page_count=len(pages),
        pages=tuple(
            ExtractedPage(page_number=index, text=text)
            for index, text in enumerate(pages, start=1)
        ),
        full_text="\n\n".join(pages),
    )


def test_split_text_into_chunks_uses_default_size_and_overlap() -> None:
    text = "".join(str(index % 10) for index in range(950))

    chunks = split_text_into_chunks(text)

    assert len(chunks) == 3
    assert chunks[0] == (text[0:500], 0, 500)
    assert chunks[1] == (text[400:900], 400, 900)
    assert chunks[2] == (text[800:950], 800, 950)
    assert chunks[0][0][-DEFAULT_CHUNK_OVERLAP:] == chunks[1][0][:DEFAULT_CHUNK_OVERLAP]
    assert len(chunks[0][0]) == DEFAULT_CHUNK_SIZE


def test_split_text_into_chunks_rejects_invalid_settings() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        split_text_into_chunks("hello", chunk_size=0, chunk_overlap=0)

    with pytest.raises(ValueError, match="smaller than chunk size"):
        split_text_into_chunks("hello", chunk_size=100, chunk_overlap=100)


def test_chunk_extracted_pdf_preserves_page_metadata(tmp_path: Path) -> None:
    extracted = _extracted_pdf(tmp_path, ["a" * 650, "b" * 200])

    chunked = chunk_extracted_pdf(extracted)

    assert chunked.chunk_size == DEFAULT_CHUNK_SIZE
    assert chunked.chunk_overlap == DEFAULT_CHUNK_OVERLAP
    assert len(chunked.chunks) == 3
    assert chunked.chunks[0].page_number == 1
    assert chunked.chunks[0].start_char == 0
    assert chunked.chunks[0].end_char == 500
    assert chunked.chunks[1].page_number == 1
    assert chunked.chunks[1].start_char == 400
    assert chunked.chunks[1].end_char == 650
    assert chunked.chunks[2].page_number == 2


def test_save_and_load_chunks(
    tmp_path: Path,
    chunks_dir: Path,
) -> None:
    extracted = _extracted_pdf(tmp_path, ["Persist chunk text"])
    chunked = chunk_extracted_pdf(extracted)

    json_path = save_chunks(chunked)

    assert json_path.parent == chunks_dir
    assert json_path.exists()

    loaded = load_chunks(extracted.source_path)
    assert loaded is not None
    assert loaded.chunks_json_path == json_path
    assert loaded.chunks == chunked.chunks


def test_chunk_and_persist_writes_json(
    tmp_path: Path,
    chunks_dir: Path,
) -> None:
    extracted = _extracted_pdf(tmp_path, ["Workflow chunk text"])

    chunked = chunk_and_persist(extracted)

    assert chunked.chunks_json_path is not None
    assert chunked.chunks_json_path.exists()
    assert chunked.chunks_json_path.parent == chunks_dir
