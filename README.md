# PDF RAG Chat

A PDF-based retrieval-augmented generation (RAG) chat application.

## Project structure

```
pdf-rag-chat/
├── app/
│   ├── api/
│   ├── services/
│   ├── rag/
│   ├── models/
│   └── utils/
├── tests/
├── docs/
├── data/
│   ├── uploads/          # locally stored uploaded PDFs
│   ├── extracted/        # extracted text saved as JSON
│   ├── chunks/           # RAG-ready text chunks saved as JSON
│   └── vector_db/        # local vector database for embeddings
├── notebooks/
├── frontend/               # Streamlit UI
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Getting started

Install dependencies:

```bash
cd pdf-rag-chat
uv sync --dev
```

Run the PDF upload UI:

```bash
uv run streamlit run frontend/ui.py
```

Upload a PDF using the drag-and-drop box or browse button. Files are saved locally under `data/uploads/`, text is extracted with **PyMuPDF** into `data/extracted/` as JSON, the extracted text is split into character chunks under `data/chunks/`, and embeddings are stored in a local JSON vector store under `data/vector_db/`.

Current chunking settings:

- Chunk size: `500` characters
- Chunk overlap: `100` characters

Current embedding settings:

- Embedding model: `BAAI/bge-small-en-v1.5`
- Embedding library: `sentence-transformers`
- Vector store: local JSON file with cosine similarity search

Current chat settings:

- Local LLM provider: Ollama
- Default Ollama model: `llama3.2`
- Override the model with `OLLAMA_MODEL`
- Override the Ollama server URL with `OLLAMA_BASE_URL`

Before asking questions, make sure Ollama is running and the model is available:

```bash
ollama pull llama3.2
ollama serve
```

Run tests:

```bash
uv run pytest
```
