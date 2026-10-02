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
    payload = response.get_json()
    result = payload["result"]
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


def test_archive_api_persists_real_cross_file_sql_candidate(client):
    test_client, _workspace_root = client
    response = test_client.post(
        "/api/v1/analysis/archive",
        data={
            "archive": (
                io.BytesIO(_zip({
                    "app/routes.py": b'''from flask import request
from services.users import find_user
def route():
    user_id = request.args.get("id")
    return find_user(user_id)
''',
                    "app/services/users.py": b'''def find_user(user_id, cursor):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return cursor.execute(query)
''',
                })),
                "project.zip",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    result = payload["result"]
    assert result["counts"]["cross_file_paths"] == 1
    assert result["counts"]["cross_file_candidates"] == 1
    finding = result["security_analysis"]["candidates"][0]
    assert finding["pack_assessment"]["pack"] == "SQL_INJECTION"
    assert finding["cross_file"] == {
        "source_file": "app/routes.py",
        "target_file": "app/services/users.py",
        "resolution": "STATIC_PYTHON_FROM_IMPORT",
    }
    lifecycle = test_client.get(
        f"/api/v1/analyses/{payload['record']['analysis_id']}"
        f"/findings/{finding['id']}/lifecycle?file=@project"
    )
    assert lifecycle.status_code == 200
    stages = {
        item["id"]: item["status"]
        for item in lifecycle.get_json()["lifecycle"]["stages"]
    }
    assert stages["TRACE"] == "OBSERVED"
    assert stages["PATCH"] == "NOT_AVAILABLE"
    assert stages["CLOSURE"] == "CLOSURE_INCOMPLETE"


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
