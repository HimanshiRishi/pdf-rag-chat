import json
from pathlib import Path

from app.core.config import ensure_chunks_dir
from app.models.schemas import ChunkedPdf, ExtractedPdf, TextChunk

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100


def _chunks_json_path(pdf_path: Path) -> Path:
    return ensure_chunks_dir() / f"{pdf_path.stem}.json"


def _validate_chunk_settings(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than 0.")
    if chunk_overlap < 0:
        raise ValueError("Chunk overlap cannot be negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[tuple[str, int, int]]:
    _validate_chunk_settings(chunk_size, chunk_overlap)

    if not text:
        return []

    chunks: list[tuple[str, int, int]] = []
    start = 0
    step = chunk_size - chunk_overlap

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append((text[start:end], start, end))

        if end == len(text):
            break

        start += step

    return chunks


def chunk_extracted_pdf(
    extracted: ExtractedPdf,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkedPdf:
    _validate_chunk_settings(chunk_size, chunk_overlap)

    chunks: list[TextChunk] = []
    chunk_index = 1

    for page in extracted.pages:
        for chunk_text, start_char, end_char in split_text_into_chunks(
            page.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ):
            chunks.append(
                TextChunk(
                    chunk_id=f"{extracted.source_path.stem}-p{page.page_number}-c{chunk_index}",
                    chunk_index=chunk_index,
                    source_path=extracted.source_path,
                    page_number=page.page_number,
                    text=chunk_text,
                    start_char=start_char,
                    end_char=end_char,
                )
            )
            chunk_index += 1

    return ChunkedPdf(
        source_path=extracted.source_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunks=tuple(chunks),
    )


def save_chunks(chunked: ChunkedPdf) -> Path:
    output_path = _chunks_json_path(chunked.source_path)
    payload = {
        "source_path": str(chunked.source_path),
        "chunk_size": chunked.chunk_size,
        "chunk_overlap": chunked.chunk_overlap,
        "chunk_count": len(chunked.chunks),
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "source_path": str(chunk.source_path),
                "page_number": chunk.page_number,
                "text": chunk.text,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            for chunk in chunked.chunks
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def chunk_and_persist(
    extracted: ExtractedPdf,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ChunkedPdf:
    chunked = chunk_extracted_pdf(
        extracted,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    json_path = save_chunks(chunked)
    return ChunkedPdf(
        source_path=chunked.source_path,
        chunk_size=chunked.chunk_size,
        chunk_overlap=chunked.chunk_overlap,
        chunks=chunked.chunks,
        chunks_json_path=json_path,
    )


def load_chunks(pdf_path: Path) -> ChunkedPdf | None:
    json_path = _chunks_json_path(pdf_path)
    if not json_path.exists():
        return None

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    chunks = tuple(
        TextChunk(
            chunk_id=chunk["chunk_id"],
            chunk_index=chunk["chunk_index"],
            source_path=Path(chunk["source_path"]),
            page_number=chunk["page_number"],
            text=chunk["text"],
            start_char=chunk["start_char"],
            end_char=chunk["end_char"],
        )
        for chunk in payload["chunks"]
    )

    return ChunkedPdf(
        source_path=Path(payload["source_path"]),
        chunk_size=payload["chunk_size"],
        chunk_overlap=payload["chunk_overlap"],
        chunks=chunks,
        chunks_json_path=json_path,
    )
