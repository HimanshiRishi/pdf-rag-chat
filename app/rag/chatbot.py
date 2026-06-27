import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.models.schemas import RagAnswer, RagSource
from app.rag.embeddings import query_similar_chunks

DEFAULT_TOP_K = 3


class RagChatError(RuntimeError):
    pass


Retriever = Callable[[str, int], dict[str, Any]]
LlmClient = Callable[[str, str], str]


def _extract_sources(retrieval_results: dict[str, Any]) -> tuple[RagSource, ...]:
    ids = retrieval_results.get("ids", [[]])[0]
    documents = retrieval_results.get("documents", [[]])[0]
    metadatas = retrieval_results.get("metadatas", [[]])[0]
    similarities = retrieval_results.get("similarities", [[]])[0]

    sources: list[RagSource] = []
    for chunk_id, document, metadata, similarity in zip(
        ids,
        documents,
        metadatas,
        similarities,
        strict=False,
    ):
        sources.append(
            RagSource(
                chunk_id=chunk_id,
                document=document,
                page_number=int(metadata["page_number"]),
                chunk_index=int(metadata["chunk_index"]),
                similarity=float(similarity),
            )
        )

    return tuple(sources)


def build_rag_prompt(question: str, sources: tuple[RagSource, ...]) -> str:
    context = "\n\n".join(
        (
            f"Source {index} "
            f"(page {source.page_number}, chunk {source.chunk_index}, "
            f"similarity {source.similarity:.3f}):\n{source.document}"
        )
        for index, source in enumerate(sources, start=1)
    )

    return f"""You are a helpful PDF question-answering assistant.
Answer the user's question using only the PDF context below.
If the context does not contain the answer, say that the PDF context does not provide enough information.
Keep the answer concise and grounded in the provided context.

PDF context:
{context}

Question:
{question}

Answer:"""


def ask_ollama(
    prompt: str,
    model_name: str = OLLAMA_MODEL,
    base_url: str = OLLAMA_BASE_URL,
) -> str:
    payload = {
        "model": model_name,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You answer questions using retrieved PDF context.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    print("=" * 50)
    print(prompt[:1000])
    print("=" * 50)
    print(f"Prompt length: {len(prompt)} chars")

    request = Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=360) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RagChatError(f"Ollama request failed: {detail}") from exc
    except URLError as exc:
        raise RagChatError(
            "Could not connect to Ollama. Start Ollama locally and make sure "
            f"`{model_name}` is available."
        ) from exc

    message = response_payload.get("message", {})
    answer = message.get("content", "").strip()
    if not answer:
        raise RagChatError("Ollama returned an empty answer.")

    return answer


def answer_question(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    retriever: Retriever | None = None,
    llm_client: LlmClient | None = None,
    model_name: str = OLLAMA_MODEL,
) -> RagAnswer:
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Question cannot be empty.")

    retrieve = retriever or query_similar_chunks
  
    generate = llm_client or ask_ollama

    retrieval_results = retrieve(clean_question, top_k)
    
    sources = _extract_sources(retrieval_results)
    if not sources:
        raise RagChatError("No indexed PDF chunks found. Upload and process a PDF first.")

    prompt = build_rag_prompt(clean_question, sources)
    answer = generate(prompt, model_name)

    return RagAnswer(
        question=clean_question,
        answer=answer,
        sources=sources,
        model_name=model_name,
    )
