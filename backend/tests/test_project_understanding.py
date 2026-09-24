from app.analysis_service import analyze_source_file
from app.project_understanding import build_project_understanding


def test_project_understanding_combines_backend_and_frontend_evidence():
    backend = analyze_source_file(
        "app.py",
        b'''from flask import Flask\napp = Flask(__name__)\n\n@app.get("/health")\ndef health():\n    return {"ok": True}\n''',
    )
    backend["artifact"]["relative_path"] = "backend/app.py"
    frontend = analyze_source_file(
        "App.jsx",
        b'''import React from "react";\nexport function App() { return <main>Ready</main>; }\n''',
    )
    frontend["artifact"]["relative_path"] = "frontend/App.jsx"

    project = build_project_understanding([backend, frontend])

    assert project["project_type"] == "FULL_STACK_PROJECT"
    assert [item["name"] for item in project["frameworks"]] == ["Flask", "React"]
    assert project["routes"][0]["path"] == "/health"
    assert project["routes"][0]["file"] == "backend/app.py"
    assert project["claims"]["cross_file_call_resolution"] == "UNRESOLVED"
    assert project["graph"]["counts"]["nodes_by_type"] == {
        "FILE": 2,
        "FRAMEWORK": 2,
        "ROUTE": 1,
    }


def test_unknown_project_stays_unknown_without_framework_evidence():
    result = analyze_source_file("task.py", b"def run():\n    return 1\n")
    result["artifact"]["relative_path"] = "task.py"

    project = build_project_understanding([result])

    assert project["project_type"] == "UNKNOWN_PROJECT"
    assert project["frameworks"] == []


def test_project_resolves_only_unique_static_local_imports():
    source = analyze_source_file(
        "app.py",
        b"from services.user import find_user\n",
    )
    source["artifact"]["relative_path"] = "backend/app.py"
    target = analyze_source_file(
        "user.py",
        b"def find_user():\n    return None\n",
    )
    target["artifact"]["relative_path"] = "backend/services/user.py"

    project = build_project_understanding([source, target])
    relationship = project["import_relationships"][0]

    assert relationship["status"] == "RESOLVED"
    assert relationship["target_file"] == "backend/services/user.py"
    assert relationship["resolution"] == "UNIQUE_PYTHON_MODULE_SUFFIX"
    assert project["graph"]["counts"]["edges_by_type"]["IMPORTS"] == 1


def test_project_leaves_ambiguous_python_import_unresolved():
    source = analyze_source_file("app.py", b"import user\n")
    source["artifact"]["relative_path"] = "app.py"
    first = analyze_source_file("user.py", b"value = 1\n")
    first["artifact"]["relative_path"] = "a/user.py"
    second = analyze_source_file("user.py", b"value = 2\n")
    second["artifact"]["relative_path"] = "b/user.py"

    project = build_project_understanding([source, first, second])

    assert project["import_relationships"][0]["status"] == "AMBIGUOUS"
    assert project["import_relationships"][0]["target_file"] is None
    assert "IMPORTS" not in project["graph"]["counts"]["edges_by_type"]
