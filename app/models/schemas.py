from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SavedPdf:
    original_name: str
    saved_path: Path
    size_bytes: int


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedPdf:
    source_path: Path
    page_count: int
    pages: tuple[ExtractedPage, ...]
    full_text: str
    extracted_json_path: Path | None = None


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    chunk_index: int
    source_path: Path
    page_number: int
    text: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class ChunkedPdf:
    source_path: Path
    chunk_size: int
    chunk_overlap: int
    chunks: tuple[TextChunk, ...]
    chunks_json_path: Path | None = None
