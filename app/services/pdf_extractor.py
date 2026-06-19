import json
from pathlib import Path

import fitz

from app.core.config import ensure_extracted_dir
from app.models.schemas import ExtractedPage, ExtractedPdf


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _extracted_json_path(pdf_path: Path) -> Path:
    return ensure_extracted_dir() / f"{pdf_path.stem}.json"


def extract_text_from_pdf(pdf_path: Path) -> ExtractedPdf:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files can be processed.")

    try:
        with fitz.open(pdf_path) as document:
            pages: list[ExtractedPage] = []

            for index, page in enumerate(document, start=1):
                raw_text = page.get_text("text")
                pages.append(
                    ExtractedPage(
                        page_number=index,
                        text=_normalize_text(raw_text),
                    )
                )

            full_text = _normalize_text("\n\n".join(page.text for page in pages if page.text))

            return ExtractedPdf(
                source_path=pdf_path,
                page_count=len(pages),
                pages=tuple(pages),
                full_text=full_text,
            )
    except fitz.FileDataError as exc:
        raise ValueError(f"Invalid or corrupted PDF: {pdf_path.name}") from exc


def save_extracted_text(extracted: ExtractedPdf) -> Path:
    output_path = _extracted_json_path(extracted.source_path)
    payload = {
        "source_path": str(extracted.source_path),
        "page_count": extracted.page_count,
        "full_text": extracted.full_text,
        "pages": [
            {"page_number": page.page_number, "text": page.text}
            for page in extracted.pages
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def extract_and_persist(pdf_path: Path) -> ExtractedPdf:
    extracted = extract_text_from_pdf(pdf_path)
    json_path = save_extracted_text(extracted)
    return ExtractedPdf(
        source_path=extracted.source_path,
        page_count=extracted.page_count,
        pages=extracted.pages,
        full_text=extracted.full_text,
        extracted_json_path=json_path,
    )


def load_extracted_text(pdf_path: Path) -> ExtractedPdf | None:
    json_path = _extracted_json_path(pdf_path)
    if not json_path.exists():
        return None

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    pages = tuple(
        ExtractedPage(page_number=page["page_number"], text=page["text"])
        for page in payload["pages"]
    )
    return ExtractedPdf(
        source_path=Path(payload["source_path"]),
        page_count=payload["page_count"],
        pages=pages,
        full_text=payload["full_text"],
        extracted_json_path=json_path,
    )
