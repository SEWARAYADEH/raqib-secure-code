import io
import zipfile

import pytest

from app import create_app


def _zip(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()

    with zipfile.ZipFile(output, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)

    return output.getvalue()


@pytest.fixture
def client(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "ANALYSIS_LOCAL_ONLY": True,
            "ANALYSIS_API_TOKEN": None,
            "WORKSPACE_ROOT": str(tmp_path / "workspaces"),
        }
    )
    return app.test_client(), tmp_path / "workspaces"


def test_archive_api_analyzes_supported_files_and_cleans_up(client):
    test_client, workspace_root = client
    response = test_client.post(
        "/api/v1/analysis/archive",
        data={
            "archive": (
                io.BytesIO(
                    _zip(
                        {
                            "backend/app.py": b"print('safe')\n",
                            "frontend/app.js": b"console.log('safe');\n",
                            "README.md": b"ignored",
                        }
                    )
                ),
                "project.zip",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    result = response.get_json()["result"]
    assert result["analysis"]["scope"] == (
        "PROJECT_STATIC_MODEL"
    )
    assert result["counts"]["analyzed_files"] == 2
    assert {
        item["artifact"]["relative_path"]
        for item in result["files"]
    } == {"backend/app.py", "frontend/app.js"}
    assert list(workspace_root.iterdir()) == []


def test_archive_api_builds_full_stack_project_understanding(client):
    test_client, _workspace_root = client
    response = test_client.post(
        "/api/v1/analysis/archive",
        data={
            "archive": (
                io.BytesIO(
                    _zip(
                        {
                            "backend/app.py": b'''from flask import Flask\napp = Flask(__name__)\n@app.get("/api/status")\ndef status():\n    return {}\n''',
                            "frontend/App.jsx": b'''import React from "react";\nexport function App() { return <main>Status</main>; }\n''',
                        }
                    )
                ),
                "project.zip",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    project = response.get_json()["result"]["project_understanding"]
    assert project["project_type"] == "FULL_STACK_PROJECT"
    assert project["routes"][0]["path"] == "/api/status"


def test_archive_api_rejects_archive_without_source(client):
    test_client, _workspace_root = client
    response = test_client.post(
        "/api/v1/analysis/archive",
        data={
            "archive": (
                io.BytesIO(_zip({"README.md": b"docs"})),
                "project.zip",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == (
        "INVALID_SOURCE_ARCHIVE"
    )


@pytest.mark.parametrize(
    "filename,content",
    [
        ("bad.py", b"\xff\xfe"),
        ("empty.py", b""),
        ("misnamed.js", b"def run():\n    return 1\n"),
    ],
)
def test_archive_api_rejects_invalid_source_members_without_server_error(
    client, filename, content
):
    test_client, workspace_root = client
    response = test_client.post(
        "/api/v1/analysis/archive",
        data={
            "archive": (
                io.BytesIO(_zip({filename: content})),
                "project.zip",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_SOURCE_ARCHIVE"
    assert list(workspace_root.iterdir()) == []
