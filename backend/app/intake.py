from __future__ import annotations

import codecs
import hashlib
from pathlib import Path


MAX_SOURCE_FILE_BYTES = 2 * 1024 * 1024


LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript JSX",
    ".ts": "TypeScript",
    ".tsx": "TypeScript TSX",
    ".php": "PHP",
    ".java": "Java",
    ".cs": "C#",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".kts": "Kotlin Script",
    ".swift": "Swift",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".ps1": "PowerShell",
}


class SourceFileValidationError(ValueError):
    pass


def inspect_source_file(
    filename: str,
    content: bytes,
) -> dict:
    safe_name = _validate_filename(filename)

    if not isinstance(content, bytes):
        raise SourceFileValidationError(
            "Source content must be provided as bytes."
        )

    size_bytes = len(content)

    if size_bytes == 0:
        raise SourceFileValidationError(
            "Source file is empty."
        )

    if size_bytes > MAX_SOURCE_FILE_BYTES:
        raise SourceFileValidationError(
            "Source file exceeds the 2 MB intake limit."
        )

    if b"\x00" in content:
        raise SourceFileValidationError(
            "Binary or null-byte content is not allowed."
        )

    source_text, encoding = _decode_source(content)

    extension = Path(safe_name).suffix.lower()

    language_hint = LANGUAGE_BY_EXTENSION.get(extension)

    line_count = len(source_text.splitlines())

    sha256 = hashlib.sha256(content).hexdigest()

    return {
        "filename": safe_name,
        "extension": extension,
        "language_hint": language_hint,
        "language_detection_method": "file_extension",
        "line_count": line_count,
        "size_bytes": size_bytes,
        "encoding": encoding,
        "sha256": sha256,
        "source_text": source_text,
    }


def _validate_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise SourceFileValidationError(
            "Filename must be a string."
        )

    filename = filename.strip()

    if not filename:
        raise SourceFileValidationError(
            "Filename is required."
        )

    if len(filename) > 255:
        raise SourceFileValidationError(
            "Filename exceeds 255 characters."
        )

    if not filename.isprintable():
        raise SourceFileValidationError(
            "Filename contains control characters."
        )

    if "/" in filename or "\\" in filename:
        raise SourceFileValidationError(
            "Filename must not contain a path."
        )

    if filename in {".", ".."}:
        raise SourceFileValidationError(
            "Invalid filename."
        )

    return filename


def _decode_source(content: bytes) -> tuple[str, str]:
    try:
        if content.startswith(codecs.BOM_UTF8):
            return content.decode("utf-8-sig"), "UTF-8 with BOM"

        return content.decode("utf-8"), "UTF-8"

    except UnicodeDecodeError as exc:
        raise SourceFileValidationError(
            "Source file must be valid UTF-8 text."
        ) from exc
