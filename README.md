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
│   └── chunks/           # RAG-ready text chunks saved as JSON
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

Upload a PDF using the drag-and-drop box or browse button. Files are saved locally under `data/uploads/`, text is extracted with **PyMuPDF** into `data/extracted/` as JSON, and the extracted text is split into character chunks under `data/chunks/`.

Current chunking settings:

- Chunk size: `500` characters
- Chunk overlap: `100` characters

Run tests:

```bash
uv run pytest
```
