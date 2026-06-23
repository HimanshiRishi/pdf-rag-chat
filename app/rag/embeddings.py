import json
import math
from pathlib import Path
from typing import Any, Protocol

from app.core.config import ensure_vector_db_dir
from app.models.schemas import ChunkedPdf, TextChunk, VectorIndexResult

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_COLLECTION_NAME = "pdf_chunks"
VECTOR_STORE_FILENAME = f"{DEFAULT_COLLECTION_NAME}.json"


class EmbeddingModel(Protocol):
    def encode(
        self,
        sentences: list[str],
        *,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> Any:
        ...


def load_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> EmbeddingModel:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "Install sentence-transformers to create embeddings: "
            "`uv add sentence-transformers`"
        ) from exc

    return SentenceTransformer(model_name)


def embed_texts(
    texts: list[str],
    model: EmbeddingModel | None = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> list[list[float]]:
    if not texts:
        return []

    embedding_model = model or load_embedding_model(model_name)
    embeddings = embedding_model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    if hasattr(embeddings, "tolist"):
        return embeddings.tolist()

    return [
        embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        for embedding in embeddings
    ]


def _vector_store_path(collection_name: str = DEFAULT_COLLECTION_NAME) -> Path:
    return ensure_vector_db_dir() / f"{collection_name}.json"


def _chunk_metadata(chunk: TextChunk, model_name: str) -> dict[str, str | int]:
    return {
        "source_path": str(chunk.source_path),
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
        "model_name": model_name,
    }


def _load_vector_store(collection_name: str = DEFAULT_COLLECTION_NAME) -> dict[str, Any]:
    store_path = _vector_store_path(collection_name)
    if not store_path.exists():
        return {"collection_name": collection_name, "items": []}

    return json.loads(store_path.read_text(encoding="utf-8"))


def _save_vector_store(
    store: dict[str, Any],
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> Path:
    store_path = _vector_store_path(collection_name)
    store_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
    return store_path


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def store_chunk_embeddings(
    chunked: ChunkedPdf,
    model: EmbeddingModel | None = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> VectorIndexResult:
    persist_directory = ensure_vector_db_dir()

    if not chunked.chunks:
        return VectorIndexResult(
            source_path=chunked.source_path,
            collection_name=collection_name,
            model_name=model_name,
            vector_count=0,
            persist_directory=persist_directory,
        )

    documents = [chunk.text for chunk in chunked.chunks]
    embeddings = embed_texts(documents, model=model, model_name=model_name)
    store = _load_vector_store(collection_name)
    existing_items = {
        item["id"]: item
        for item in store.get("items", [])
        if item.get("source_path") != str(chunked.source_path)
    }

    for chunk, document, embedding in zip(chunked.chunks, documents, embeddings, strict=True):
        existing_items[chunk.chunk_id] = {
            "id": chunk.chunk_id,
            "source_path": str(chunked.source_path),
            "document": document,
            "embedding": embedding,
            "metadata": _chunk_metadata(chunk, model_name),
        }

    store = {
        "collection_name": collection_name,
        "embedding_model": model_name,
        "similarity": "cosine",
        "items": list(existing_items.values()),
    }
    _save_vector_store(store, collection_name)

    return VectorIndexResult(
        source_path=chunked.source_path,
        collection_name=collection_name,
        model_name=model_name,
        vector_count=len(chunked.chunks),
        persist_directory=persist_directory,
    )


def query_similar_chunks(
    question: str,
    top_k: int = 3,
    model: EmbeddingModel | None = None,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> dict[str, Any]:
    query_embedding = embed_texts([question], model=model, model_name=model_name)[0]
    store = _load_vector_store(collection_name)
    scored_items = []

    for item in store.get("items", []):
        score = _cosine_similarity(query_embedding, item["embedding"])
        scored_items.append((score, item))

    scored_items.sort(key=lambda pair: pair[0], reverse=True)
    matches = scored_items[:top_k]

    return {
        "ids": [[item["id"] for _, item in matches]],
        "documents": [[item["document"] for _, item in matches]],
        "metadatas": [[item["metadata"] for _, item in matches]],
        "similarities": [[score for score, _ in matches]],
    }
