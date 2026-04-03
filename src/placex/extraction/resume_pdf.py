from __future__ import annotations

from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF resume using pdfplumber.
    Best-effort: if a PDF page fails, we continue.
    """
    from pdfplumber import open as pdf_open  # lazy import

    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    all_text: list[str] = []
    with pdf_open(str(p)) as pdf:
        for page in pdf.pages:
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t.strip():
                all_text.append(t)

    return "\n".join(all_text).strip()

