import streamlit as st

from app.rag.chunker import chunk_and_persist, load_chunks
from app.rag.embeddings import store_chunk_embeddings
from app.services.pdf_extractor import extract_and_persist, load_extracted_text
from app.services.pdf_storage import list_saved_pdfs, save_pdf
from frontend.styles import UPLOAD_BOX_CSS


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def render_upload_box() -> None:
    st.markdown(UPLOAD_BOX_CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="upload-header">
            <h1>Upload PDF</h1>
            <p>Add a document to start chatting with your PDF.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="upload-placeholder">
            <div class="pdf-icon">📄</div>
            <div class="title">Drop your PDF here</div>
            <div class="subtitle">or click Browse files below</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="pdf_uploader",
    )

    if uploaded_file is None:
        return

    if uploaded_file.name in st.session_state.get("saved_uploads", set()):
        st.info(f"`{uploaded_file.name}` is already saved in this session.")
        return

    try:
        saved = save_pdf(uploaded_file.getvalue(), uploaded_file.name)
        extracted = extract_and_persist(saved.saved_path)
        chunked = chunk_and_persist(extracted)
        vector_index = store_chunk_embeddings(chunked)
    except ValueError as exc:
        st.error(str(exc))
        return
    except ImportError as exc:
        st.error(str(exc))
        return
    except OSError as exc:
        st.error(f"Failed to process PDF: {exc}")
        return

    saved_uploads = st.session_state.setdefault("saved_uploads", set())
    saved_uploads.add(uploaded_file.name)

    st.success(
        f"Saved **{saved.original_name}** to `{saved.saved_path}` "
        f"({_format_size(saved.size_bytes)})"
    )
    st.info(
        f"Extracted **{extracted.page_count}** page(s) "
        f"({len(extracted.full_text):,} characters)"
    )
    st.info(
        f"Created **{len(chunked.chunks)}** chunk(s) "
        f"with size **{chunked.chunk_size}** and overlap **{chunked.chunk_overlap}**"
    )
    st.info(
        f"Stored **{vector_index.vector_count}** embedding vector(s) "
        f"in `{vector_index.collection_name}` using `{vector_index.model_name}`"
    )

    if extracted.full_text:
        with st.expander("Preview extracted text"):
            preview = extracted.full_text[:2000]
            st.text(preview + ("..." if len(extracted.full_text) > 2000 else ""))

    if chunked.chunks:
        with st.expander("Preview chunks"):
            for chunk in chunked.chunks[:3]:
                st.markdown(
                    f"**Chunk {chunk.chunk_index}** · page {chunk.page_number} · "
                    f"chars {chunk.start_char}-{chunk.end_char}"
                )
                st.text(chunk.text)


def render_saved_files() -> None:
    saved_pdfs = list_saved_pdfs()
    if not saved_pdfs:
        return

    st.subheader("Saved PDFs")
    for pdf in saved_pdfs:
        extracted = load_extracted_text(pdf.saved_path)
        chunked = load_chunks(pdf.saved_path)
        extraction_note = ""
        if extracted:
            extraction_note = (
                f"<br/><span style='color:#8ba4b8;font-size:0.85rem;'>"
                f"{extracted.page_count} page(s) extracted · "
                f"{len(extracted.full_text):,} characters"
                f"</span>"
            )
        chunk_note = ""
        if chunked:
            chunk_note = (
                f"<br/><span style='color:#8ba4b8;font-size:0.85rem;'>"
                f"{len(chunked.chunks)} chunk(s) · "
                f"size {chunked.chunk_size} · overlap {chunked.chunk_overlap}"
                f"</span>"
            )

        st.markdown(
            f"""
            <div class="saved-file-card">
                <strong>{pdf.original_name}</strong><br/>
                <span style="color:#7a8794;font-size:0.9rem;">
                    {_format_size(pdf.size_bytes)} · {pdf.saved_path}
                </span>
                {extraction_note}
                {chunk_note}
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="PDF RAG Chat",
        page_icon="📄",
        layout="centered",
    )

    render_upload_box()
    render_saved_files()


if __name__ == "__main__":
    main()
