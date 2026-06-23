from pathlib import Path

import pytest

from app.models.schemas import ChunkedPdf, TextChunk
from app.rag.embeddings import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    embed_texts,
    query_similar_chunks,
    store_chunk_embeddings,
)


class FakeEmbedding:
    def __init__(self, values: list[float]) -> None:
        self.values = values

    def tolist(self) -> list[float]:
        return self.values


class FakeModel:
    def encode(
        self,
        sentences: list[str],
        *,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> list[FakeEmbedding]:
        assert normalize_embeddings is True
        assert show_progress_bar is False
        return [
            FakeEmbedding([float(index), float(len(sentence))])
            for index, sentence in enumerate(sentences, start=1)
        ]


@pytest.fixture
def vector_db_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "vector_db"
    monkeypatch.setattr("app.core.config.VECTOR_DB_DIR", target)
    return target


def _chunked_pdf(tmp_path: Path) -> ChunkedPdf:
    source_path = tmp_path / "sample.pdf"
    return ChunkedPdf(
        source_path=source_path,
        chunk_size=500,
        chunk_overlap=100,
        chunks=(
            TextChunk(
                chunk_id="sample-p1-c1",
                chunk_index=1,
                source_path=source_path,
                page_number=1,
                text="first chunk about machine learning",
                start_char=0,
                end_char=34,
            ),
            TextChunk(
                chunk_id="sample-p1-c2",
                chunk_index=2,
                source_path=source_path,
                page_number=1,
                text="second chunk about vector search",
                start_char=400,
                end_char=432,
            ),
        ),
    )


def test_embed_texts_uses_normalized_sentence_transformer_embeddings() -> None:
    embeddings = embed_texts(["hello", "semantic search"], model=FakeModel())

    assert embeddings == [[1.0, 5.0], [2.0, 15.0]]


def test_store_chunk_embeddings_writes_vectors_to_collection(
    tmp_path: Path,
    vector_db_dir: Path,
) -> None:
    chunked = _chunked_pdf(tmp_path)

    result = store_chunk_embeddings(
        chunked,
        model=FakeModel(),
    )

    assert result.collection_name == DEFAULT_COLLECTION_NAME
    assert result.model_name == DEFAULT_EMBEDDING_MODEL
    assert result.vector_count == 2
    assert result.persist_directory == vector_db_dir
    store_path = vector_db_dir / f"{DEFAULT_COLLECTION_NAME}.json"
    assert store_path.exists()

    store = store_path.read_text(encoding="utf-8")
    assert "first chunk about machine learning" in store
    assert "second chunk about vector search" in store
    assert DEFAULT_EMBEDDING_MODEL in store


def test_query_similar_chunks_embeds_question_and_queries_collection(
    tmp_path: Path,
    vector_db_dir: Path,
) -> None:
    store_chunk_embeddings(_chunked_pdf(tmp_path), model=FakeModel())

    results = query_similar_chunks(
        "What is vector search?",
        top_k=1,
        model=FakeModel(),
    )

    assert len(results["ids"][0]) == 1
    assert len(results["documents"][0]) == 1
    assert len(results["metadatas"][0]) == 1
    assert len(results["similarities"][0]) == 1
