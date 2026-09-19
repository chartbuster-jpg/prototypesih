from io import BytesIO


def extract_text_from_upload(filename: str, content: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        parts = []
        for page in reader.pages[:30]:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()

    if name.endswith(".docx"):
        from docx import Document

        doc = Document(BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs).strip()

    try:
        return content.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
