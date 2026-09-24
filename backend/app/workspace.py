from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path, PurePosixPath


class WorkspacePathError(ValueError):
    pass


class AnalysisWorkspace:
    """Temporary isolated directory for untrusted analysis artifacts."""

    def __init__(self, root: str) -> None:
        self.base_root = Path(root).resolve()
        self.path: Path | None = None

    def __enter__(self) -> "AnalysisWorkspace":
        self.base_root.mkdir(
            mode=0o700,
            parents=True,
            exist_ok=True,
        )
        self.path = self.base_root / str(uuid.uuid4())
        self.path.mkdir(mode=0o700)
        return self

    def __exit__(self, _type, _value, _traceback) -> None:
        self.cleanup()

    def write_bytes(
        self,
        relative_path: str,
        content: bytes,
    ) -> Path:
        target = self.resolve_target(relative_path)
        target.parent.mkdir(
            mode=0o700,
            parents=True,
            exist_ok=True,
        )

        with target.open("xb") as stream:
            stream.write(content)

        try:
            os.chmod(target, 0o600)
        except OSError:
            pass

        return target

    def resolve_target(self, relative_path: str) -> Path:
        if self.path is None:
            raise RuntimeError("Workspace is not active.")

        normalized = _validated_relative_path(relative_path)
        target = (self.path / Path(*normalized.parts)).resolve()

        if not target.is_relative_to(self.path):
            raise WorkspacePathError(
                "Workspace target escapes its isolated root."
            )

        return target

    def cleanup(self) -> None:
        if self.path is None or not self.path.exists():
            return

        resolved = self.path.resolve()

        if (
            resolved.parent != self.base_root
            or resolved == self.base_root
        ):
            raise RuntimeError(
                "Refusing to remove an unverified workspace path."
            )

        shutil.rmtree(resolved)
        self.path = None


def _validated_relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise WorkspacePathError("Archive path is required.")

    if "\\" in value or "\x00" in value:
        raise WorkspacePathError(
            "Archive paths must use safe POSIX separators."
        )

    path = PurePosixPath(value)

    if path.is_absolute() or any(
        part in {"", ".", ".."}
        for part in path.parts
    ):
        raise WorkspacePathError(
            "Archive path must be relative and normalized."
        )

    if len(path.parts) > 12:
        raise WorkspacePathError(
            "Archive path exceeds the depth limit."
        )

    for part in path.parts:
        if (
            len(part) > 255
            or not part.isprintable()
            or part.endswith((" ", "."))
            or ":" in part
            or _is_windows_reserved(part)
        ):
            raise WorkspacePathError(
                "Archive path contains an unsafe component."
            )

    return path


def _is_windows_reserved(value: str) -> bool:
    stem = value.split(".", 1)[0].casefold()
    reserved = {"con", "prn", "aux", "nul"}
    reserved.update(f"com{index}" for index in range(1, 10))
    reserved.update(f"lpt{index}" for index in range(1, 10))
    return stem in reserved
