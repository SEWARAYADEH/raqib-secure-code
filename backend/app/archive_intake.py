from __future__ import annotations

import hashlib
import io
import stat
import zipfile
from pathlib import Path

from app.intake import MAX_SOURCE_FILE_BYTES
from app.workspace import (
    AnalysisWorkspace,
    WorkspacePathError,
)


MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 1_000
MAX_SOURCE_FILES = 100
MAX_TOTAL_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 20 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
SOURCE_EXTENSIONS = {".py", ".js", ".jsx"}
NESTED_ARCHIVE_EXTENSIONS = {
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
}


class SourceArchiveValidationError(ValueError):
    pass


def extract_source_archive(
    *,
    filename: str,
    content: bytes,
    workspace: AnalysisWorkspace,
) -> dict:
    _validate_archive_name(filename)

    if not isinstance(content, bytes):
        raise SourceArchiveValidationError(
            "Archive content must be bytes."
        )

    if not content or len(content) > MAX_ARCHIVE_BYTES:
        raise SourceArchiveValidationError(
            "Archive size is outside the allowed range."
        )

    buffer = io.BytesIO(content)

    if not zipfile.is_zipfile(buffer):
        raise SourceArchiveValidationError(
            "The uploaded file is not a valid ZIP archive."
        )

    files = []
    canonical_paths = set()
    total_expanded = 0
    total_source = 0

    try:
        with zipfile.ZipFile(buffer) as archive:
            members = archive.infolist()

            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise SourceArchiveValidationError(
                    "Archive exceeds the member-count limit."
                )

            for member in members:
                relative_path = member.filename

                try:
                    target = workspace.resolve_target(relative_path)
                except WorkspacePathError as exc:
                    raise SourceArchiveValidationError(
                        str(exc)
                    ) from exc

                canonical = relative_path.casefold()

                if canonical in canonical_paths:
                    raise SourceArchiveValidationError(
                        "Archive contains colliding paths."
                    )

                canonical_paths.add(canonical)

                if member.is_dir():
                    continue

                if member.flag_bits & 0x1:
                    raise SourceArchiveValidationError(
                        "Encrypted archive members are not accepted."
                    )

                unix_mode = member.external_attr >> 16

                if stat.S_ISLNK(unix_mode):
                    raise SourceArchiveValidationError(
                        "Symbolic links are not accepted."
                    )

                total_expanded += member.file_size

                if total_expanded > MAX_TOTAL_EXPANDED_BYTES:
                    raise SourceArchiveValidationError(
                        "Archive exceeds the expanded-size limit."
                    )

                ratio = member.file_size / max(
                    member.compress_size,
                    1,
                )

                if ratio > MAX_COMPRESSION_RATIO:
                    raise SourceArchiveValidationError(
                        "Archive contains an unsafe compression ratio."
                    )

                extension = Path(relative_path).suffix.lower()

                if extension in NESTED_ARCHIVE_EXTENSIONS:
                    raise SourceArchiveValidationError(
                        "Nested archives are not accepted."
                    )

                if extension not in SOURCE_EXTENSIONS:
                    continue

                if member.file_size > MAX_SOURCE_FILE_BYTES:
                    raise SourceArchiveValidationError(
                        "A source member exceeds the per-file limit."
                    )

                if len(files) >= MAX_SOURCE_FILES:
                    raise SourceArchiveValidationError(
                        "Archive exceeds the source-file limit."
                    )

                source = _read_bounded_member(archive, member)
                total_source += len(source)

                if total_source > MAX_TOTAL_SOURCE_BYTES:
                    raise SourceArchiveValidationError(
                        "Archive exceeds the total source-size limit."
                    )

                workspace.write_bytes(relative_path, source)
                files.append(
                    {
                        "relative_path": relative_path,
                        "workspace_path": str(target),
                        "size_bytes": len(source),
                        "sha256": hashlib.sha256(
                            source
                        ).hexdigest(),
                    }
                )
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise SourceArchiveValidationError(
            "The ZIP archive could not be read safely."
        ) from exc

    if not files:
        raise SourceArchiveValidationError(
            "Archive contains no supported source files."
        )

    return {
        "filename": filename,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "source_file_count": len(files),
        "total_source_bytes": total_source,
        "files": files,
    }


def _read_bounded_member(
    archive: zipfile.ZipFile,
    member: zipfile.ZipInfo,
) -> bytes:
    with archive.open(member, "r") as stream:
        content = stream.read(MAX_SOURCE_FILE_BYTES + 1)

    if len(content) > MAX_SOURCE_FILE_BYTES:
        raise SourceArchiveValidationError(
            "A source member exceeds the per-file limit."
        )

    if len(content) != member.file_size:
        raise SourceArchiveValidationError(
            "Archive member size does not match its metadata."
        )

    return content


def _validate_archive_name(filename: str) -> None:
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > 255
        or not filename.isprintable()
        or "/" in filename
        or "\\" in filename
        or Path(filename).suffix.lower() != ".zip"
    ):
        raise SourceArchiveValidationError(
            "Archive filename must be a safe .zip basename."
        )
