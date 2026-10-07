"""Run as a bounded subprocess; never execute document actions or embedded code."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfReader, apply_configuration


@apply_configuration(maximum_declared_stream_length=16 * 1024**2,
                     array_based_stream_maximum_output_length=16 * 1024**2,
                     zlib_maximum_output_length=16 * 1024**2,
                     lzw_maximum_output_length=16 * 1024**2,
                     run_length_maximum_output_length=16 * 1024**2,
                     image_maximum_buffer_size=16 * 1024**2,
                     page_tree_maximum_entries=2000, xform_maximum_invocations_per_extraction=500,
                     jbig2dec_binary=None)
def extract(path: Path) -> list[str]:
    reader = PdfReader(path, strict=True)
    if reader.is_encrypted:
        raise ValueError("ENCRYPTED_PDF")
    if not 1 <= len(reader.pages) <= 100:
        raise ValueError("PAGE_LIMIT")
    pages = []
    characters = 0
    weak_pages = 0
    for page in reader.pages:
        if "/EmbeddedFiles" in str(reader.trailer.get("/Root", {})):
            raise ValueError("EMBEDDED_FILES_UNSUPPORTED")
        text = page.extract_text() or ""
        text = "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()
        if "\ufffd" in text or "\x00" in text:
            raise ValueError("UNUSABLE_PDF_TEXT")
        characters += len(text)
        if characters > 500000:
            raise ValueError("PDF_TEXT_LIMIT")
        if len(text) < 20 and page.images:
            weak_pages += 1
        pages.append(text)
    if sum(len(text.strip()) for text in pages) < 20:
        raise ValueError("NO_EXTRACTABLE_TEXT")
    if weak_pages:
        raise ValueError("OCR_REQUIRED")
    return pages


if __name__ == "__main__":
    try:
        print(json.dumps({"pages": extract(Path(sys.argv[1]))}, ensure_ascii=True))
    except Exception as exc:
        code = str(exc) if isinstance(exc, ValueError) else "CORRUPT_PDF"
        print(json.dumps({"error": code}))
        sys.exit(2)
