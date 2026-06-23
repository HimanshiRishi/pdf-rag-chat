from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXTRACTED_DIR = DATA_DIR / "extracted"
CHUNKS_DIR = DATA_DIR / "chunks"
VECTOR_DB_DIR = DATA_DIR / "vector_db"


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def ensure_extracted_dir() -> Path:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    return EXTRACTED_DIR


def ensure_chunks_dir() -> Path:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    return CHUNKS_DIR


def ensure_vector_db_dir() -> Path:
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    return VECTOR_DB_DIR
