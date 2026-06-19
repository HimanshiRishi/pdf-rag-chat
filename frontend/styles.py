UPLOAD_BOX_CSS = """
<style>
:root {
    --bg-page: #f5f6f8;
    --bg-surface: #ffffff;
    --bg-muted: #eef1f5;
    --text-primary: #3d4852;
    --text-secondary: #7a8794;
    --text-muted: #9aa5b1;
    --border-soft: #e4e8ec;
    --accent: #8ba4b8;
    --accent-soft: #e8eef3;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: var(--bg-page);
    color: var(--text-primary);
}

.block-container {
    padding-top: 2rem;
    max-width: 720px;
}

h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: var(--text-primary);
}

[data-testid="stMarkdownContainer"] code {
    background-color: var(--bg-muted);
    color: #5c6b7a;
    border: 1px solid var(--border-soft);
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
}

.upload-header {
    text-align: center;
    margin-bottom: 0.5rem;
}

.upload-header h1 {
    font-size: 1.75rem;
    margin-bottom: 0.25rem;
    color: var(--text-primary);
    font-weight: 600;
}

.upload-header p {
    color: var(--text-secondary);
    margin-top: 0;
}

[data-testid="stFileUploader"] {
    padding: 0;
}

[data-testid="stFileUploader"] section {
    border: 2px dashed var(--border-soft);
    border-radius: 16px;
    background: var(--bg-surface);
    padding: 2.5rem 1.5rem;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
    box-shadow: 0 1px 3px rgba(61, 72, 82, 0.04);
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent);
    background: var(--accent-soft);
    box-shadow: 0 4px 12px rgba(139, 164, 184, 0.12);
}

[data-testid="stFileUploader"] section > div {
    width: 100%;
    text-align: center;
}

[data-testid="stFileUploader"] label {
    display: none;
}

[data-testid="stFileUploader"] button,
[data-testid="baseButton-secondary"] {
    margin-top: 0.75rem;
    border-radius: 8px;
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-soft) !important;
}

[data-testid="stFileUploader"] button:hover,
[data-testid="baseButton-secondary"]:hover {
    border-color: var(--accent) !important;
    background-color: var(--accent-soft) !important;
    color: var(--text-primary) !important;
}

.upload-placeholder {
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 0.75rem;
}

.upload-placeholder .pdf-icon {
    font-size: 3rem;
    line-height: 1;
    margin-bottom: 0.75rem;
    opacity: 0.85;
}

.upload-placeholder .title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
    color: var(--text-primary);
}

.upload-placeholder .subtitle {
    font-size: 0.95rem;
    color: var(--text-muted);
}

.saved-file-card {
    border: 1px solid var(--border-soft);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    background: var(--bg-surface);
    box-shadow: 0 1px 2px rgba(61, 72, 82, 0.04);
}

.saved-file-card strong {
    color: var(--text-primary);
}

[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid var(--border-soft);
}
</style>
"""
