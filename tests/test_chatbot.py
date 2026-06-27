import json
from urllib.error import URLError

import pytest

from app.models.schemas import RagSource
from app.rag.chatbot import (
    RagChatError,
    answer_question,
    ask_ollama,
    build_rag_prompt,
)


def _retrieval_results() -> dict[str, object]:
    return {
        "ids": [["sample-p1-c1"]],
        "documents": [["PDF context about semantic search."]],
        "metadatas": [[{"page_number": 1, "chunk_index": 1}]],
        "similarities": [[0.91]],
    }


def test_build_rag_prompt_includes_question_and_sources() -> None:
    prompt = build_rag_prompt(
        "What is semantic search?",
        (
            RagSource(
                chunk_id="sample-p1-c1",
                document="Semantic search compares meaning.",
                page_number=1,
                chunk_index=1,
                similarity=0.91,
            ),
        ),
    )

    assert "What is semantic search?" in prompt
    assert "Semantic search compares meaning." in prompt
    assert "using only the PDF context" in prompt


def test_answer_question_retrieves_context_and_calls_llm() -> None:
    captured = {}

    def fake_retriever(question: str, top_k: int) -> dict[str, object]:
        captured["question"] = question
        captured["top_k"] = top_k
        return _retrieval_results()

    def fake_llm(prompt: str, model_name: str) -> str:
        captured["prompt"] = prompt
        captured["model_name"] = model_name
        return "Semantic search finds chunks with similar meaning."

    answer = answer_question(
        " What is semantic search? ",
        top_k=1,
        retriever=fake_retriever,
        llm_client=fake_llm,
        model_name="llama3.2",
    )

    assert answer.question == "What is semantic search?"
    assert answer.answer == "Semantic search finds chunks with similar meaning."
    assert answer.model_name == "llama3.2"
    assert answer.sources[0].page_number == 1
    assert captured["question"] == "What is semantic search?"
    assert captured["top_k"] == 1
    assert "PDF context about semantic search." in captured["prompt"]


def test_answer_question_requires_indexed_chunks() -> None:
    def fake_retriever(question: str, top_k: int) -> dict[str, object]:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "similarities": [[]]}

    with pytest.raises(RagChatError, match="No indexed PDF chunks"):
        answer_question("What is this?", retriever=fake_retriever)


def test_ask_ollama_posts_chat_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def read(self) -> bytes:
            return json.dumps({"message": {"content": "Grounded answer"}}).encode("utf-8")

    def fake_urlopen(request, timeout: int):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr("app.rag.chatbot.urlopen", fake_urlopen)

    answer = ask_ollama(
        "Prompt text",
        model_name="llama3.2",
        base_url="http://localhost:11434",
    )

    assert answer == "Grounded answer"
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["timeout"] == 120
    assert captured["payload"]["model"] == "llama3.2"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["messages"][1]["content"] == "Prompt text"


def test_ask_ollama_raises_when_local_server_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request, timeout: int):
        raise URLError("connection refused")

    monkeypatch.setattr("app.rag.chatbot.urlopen", fake_urlopen)

    with pytest.raises(RagChatError, match="Could not connect to Ollama"):
        ask_ollama("Prompt text")
