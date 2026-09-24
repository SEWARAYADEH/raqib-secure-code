import io
import stat
import zipfile

import pytest

from app.archive_intake import (
    SourceArchiveValidationError,
    extract_source_archive,
)
from app.workspace import (
    AnalysisWorkspace,
    WorkspacePathError,
)


def _zip(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()

    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)

    return output.getvalue()


def test_safe_sources_extract_inside_temporary_workspace(tmp_path):
    root = tmp_path / "workspaces"

    with AnalysisWorkspace(str(root)) as workspace:
        active_path = workspace.path
        result = extract_source_archive(
            filename="project.zip",
            content=_zip(
                {
                    "src/app.py": b"print('safe')\n",
                    "src/app.js": b"console.log('safe');\n",
                    "README.md": b"documentation",
                }
            ),
            workspace=workspace,
        )

        assert result["source_file_count"] == 2
        assert (active_path / "src" / "app.py").is_file()
        assert not (active_path / "README.md").exists()

    assert not active_path.exists()


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "../escape.py",
        "/absolute.py",
        "src/../../escape.py",
        "CON.py",
        "src/trailing./app.py",
    ],
)
def test_unsafe_archive_paths_are_rejected(
    tmp_path,
    unsafe_path,
):
    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(SourceArchiveValidationError):
            extract_source_archive(
                filename="project.zip",
                content=_zip(
                    {unsafe_path: b"print('unsafe')\n"}
                ),
                workspace=workspace,
            )


def test_case_colliding_paths_are_rejected(tmp_path):
    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(
            SourceArchiveValidationError,
            match="colliding",
        ):
            extract_source_archive(
                filename="project.zip",
                content=_zip(
                    {
                        "src/App.py": b"a = 1\n",
                        "src/app.py": b"a = 2\n",
                    }
                ),
                workspace=workspace,
            )


def test_symbolic_link_member_is_rejected(tmp_path):
    output = io.BytesIO()
    link = zipfile.ZipInfo("src/link.py")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16

    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(link, "../../outside.py")

    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(
            SourceArchiveValidationError,
            match="Symbolic links",
        ):
            extract_source_archive(
                filename="project.zip",
                content=output.getvalue(),
                workspace=workspace,
            )


def test_unsafe_compression_ratio_is_rejected(tmp_path):
    content = _zip({"zeros.py": b"0" * (1024 * 1024)})

    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(
            SourceArchiveValidationError,
            match="compression ratio",
        ):
            extract_source_archive(
                filename="project.zip",
                content=content,
                workspace=workspace,
            )


def test_nested_archive_is_rejected(tmp_path):
    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(
            SourceArchiveValidationError,
            match="Nested archives",
        ):
            extract_source_archive(
                filename="project.zip",
                content=_zip(
                    {
                        "src/app.py": b"a = 1\n",
                        "nested.zip": b"not-really-a-zip",
                    }
                ),
                workspace=workspace,
            )


def test_workspace_rejects_path_before_activation(tmp_path):
    workspace = AnalysisWorkspace(str(tmp_path))

    with pytest.raises(RuntimeError, match="not active"):
        workspace.resolve_target("src/app.py")


def test_workspace_rejects_direct_traversal(tmp_path):
    with AnalysisWorkspace(str(tmp_path)) as workspace:
        with pytest.raises(WorkspacePathError):
            workspace.resolve_target("../outside.py")
