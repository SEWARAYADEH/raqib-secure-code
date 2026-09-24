import io
import zipfile

from app.archive_service import analyze_source_archive
from app.manifest_intelligence import inspect_manifest


def _archive(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in entries.items():
            archive.writestr(path, content)
    return output.getvalue()


def test_project_reads_declarations_without_claiming_sca(tmp_path):
    result = analyze_source_archive(
        filename="project.zip",
        content=_archive(
            {
                "app.py": b"from flask import Flask\napp = Flask(__name__)\n",
                "requirements.txt": b"Flask==3.1.3\n-r private.txt\n",
                "ui/package.json": (
                    b'{"dependencies":{"react":"18.2.0","x":"^1.0.0"}}'
                ),
                "ui/App.jsx": (
                    b'import React from "react";\n'
                    b'export function App() { return <main>Ready</main>; }\n'
                ),
            }
        ),
        workspace_root=str(tmp_path),
    )
    project = result["project_understanding"]

    assert project["counts"]["manifests"] == 2
    assert project["counts"]["dependency_declarations"] == 3
    assert project["claims"]["sca_vulnerability_check"] == "NOT_RUN"
    assert project["graph"]["counts"]["nodes_by_type"]["MANIFEST"] == 2
    assert project["graph"]["counts"]["edges_by_type"][
        "DECLARES_DEPENDENCY"
    ] == 3
    react = next(
        item for item in project["frameworks"] if item["name"] == "React"
    )
    assert react["status"] == "CORROBORATED"
    assert react["runtime_verified"] is False
    assert "MANIFEST_DECLARATION" in react["evidence_signals"]
    assert all(
        "private.txt" not in str(item)
        for item in project["dependency_declarations"]
    )
    assert any(
        item["name"] == "x" and item["version"] is None
        for item in project["dependency_declarations"]
    )


def test_duplicate_json_keys_do_not_produce_dependency_claims():
    manifest = inspect_manifest(
        "package.json",
        b'{"dependencies":{"a":"1.0.0"},"dependencies":{"b":"2.0.0"}}',
    )

    assert manifest["status"] == "INVALID_MANIFEST"
    assert manifest["dependencies"] == []
