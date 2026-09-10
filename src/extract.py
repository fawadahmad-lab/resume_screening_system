"""Deterministic text extraction from PDF, DOCX, and TXT files."""

import os
import logging

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """Extract plain text from a resume file.

    Supports .txt, .pdf, and .docx formats.
    Never uses an LLM — purely deterministic extraction.

    Args:
        file_path: Path to the resume file.

    Returns:
        Extracted plain text.

    Raises:
        ValueError: If the file format is unsupported.
        FileNotFoundError: If the file does not exist.
        RuntimeError: If extraction fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".txt":
            return _extract_txt(file_path)
        elif ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext == ".docx":
            return _extract_docx(file_path)
        else:
            raise ValueError(
                f"Unsupported file format '{ext}'. "
                "Supported formats: .txt, .pdf, .docx"
            )
    except (ValueError, FileNotFoundError):
        raise
    except Exception as e:
        raise RuntimeError(
            f"Failed to extract text from {file_path}: {e}"
        ) from e


def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()


def _extract_pdf(file_path: str) -> str:
    import pdfplumber

    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

    result = "\n\n".join(pages).strip()
    if not result:
        raise RuntimeError(f"PDF extraction returned empty text: {file_path}")
    return result


def _extract_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    result = "\n\n".join(paragraphs).strip()
    if not result:
        raise RuntimeError(f"DOCX extraction returned empty text: {file_path}")
    return result
