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
    node_counts = project["graph"]["counts"]["nodes_by_type"]
    assert node_counts["FILE"] == 2
    assert node_counts["FRAMEWORK"] == 2
    assert node_counts["ROUTE"] == 1
    assert node_counts["FUNCTION"] == 2


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


def test_project_resolves_unshadowed_imported_python_function_call():
    source = analyze_source_file(
        "app.py",
        b"from services.user import find_user as lookup\ndef route():\n    return lookup()\n",
    )
    source["artifact"]["relative_path"] = "backend/app.py"
    target = analyze_source_file("user.py", b"def find_user():\n    return 1\n")
    target["artifact"]["relative_path"] = "backend/services/user.py"

    project = build_project_understanding([source, target])

    assert len(project["cross_file_calls"]) == 1
    assert project["cross_file_calls"][0]["callee"] == "find_user"
    assert project["cross_file_calls"][0]["resolution"] == "STATIC_PYTHON_FROM_IMPORT"
    assert project["claims"]["cross_file_call_resolution"] == "PARTIAL_STATIC"
    assert project["claims"]["cross_file_call_languages"] == ["Python"]
    assert project["claims"]["cross_file_data_flow"] == "UNRESOLVED"
    assert project["graph"]["counts"]["edges_by_type"]["CALLS"] == 1


def test_project_resolves_unshadowed_python_module_alias_call():
    source = analyze_source_file(
        "app.py",
        b"import services.user as users\ndef route():\n    return users.find_user()\n",
    )
    source["artifact"]["relative_path"] = "backend/app.py"
    target = analyze_source_file("user.py", b"def find_user():\n    return 1\n")
    target["artifact"]["relative_path"] = "backend/services/user.py"

    project = build_project_understanding([source, target])

    assert project["import_relationships"][0]["module"] == "services.user"
    assert project["cross_file_calls"][0]["call_target"] == "users.find_user"
    assert project["cross_file_calls"][0]["resolution"] == (
        "STATIC_PYTHON_MODULE_IMPORT"
    )


def test_project_resolves_full_python_module_call():
    source = analyze_source_file(
        "app.py",
        b"import services.user\ndef route():\n    return services.user.find_user()\n",
    )
    source["artifact"]["relative_path"] = "backend/app.py"
    target = analyze_source_file("user.py", b"def find_user():\n    return 1\n")
    target["artifact"]["relative_path"] = "backend/services/user.py"

    project = build_project_understanding([source, target])
    assert project["cross_file_calls"][0]["call_target"] == (
        "services.user.find_user"
    )


def test_project_does_not_resolve_shadowed_or_ambiguous_imported_call():
    source = analyze_source_file(
        "app.py",
        b"from services.user import find_user\ndef route(find_user):\n    return find_user()\n",
    )
    source["artifact"]["relative_path"] = "backend/app.py"
    target = analyze_source_file("user.py", b"def find_user():\n    return 1\n")
    target["artifact"]["relative_path"] = "backend/services/user.py"
    ambiguous = analyze_source_file("user.py", b"def find_user():\n    return 2\n")
    ambiguous["artifact"]["relative_path"] = "other/services/user.py"

    for files in ([source, target], [source, target, ambiguous]):
        project = build_project_understanding(files)
        assert project["cross_file_calls"] == []
        assert "CALLS" not in project["graph"]["counts"]["edges_by_type"]


def test_project_rejects_rebound_python_import_binding():
    target = analyze_source_file("user.py", b"def find_user():\n    return 1\n")
    target["artifact"]["relative_path"] = "services/user.py"
    sources = (
        b"from services.user import find_user\ndef route():\n    for find_user in []:\n        pass\n    return find_user()\n",
        b"from services.user import find_user\nfind_user = None\ndef route():\n    return find_user()\n",
        b"def setup():\n    from services.user import find_user\ndef route():\n    return find_user()\n",
    )
    for content in sources:
        source = analyze_source_file("app.py", content)
        source["artifact"]["relative_path"] = "app.py"
        project = build_project_understanding([source, target])
        assert project["cross_file_calls"] == []


def test_project_resolves_static_javascript_named_import_call():
    source = analyze_source_file(
        "main.js",
        b'import { findUser as lookup } from "./user.js";\n'
        b'export function main() { return lookup(); }\n',
    )
    source["artifact"]["relative_path"] = "src/main.js"
    target = analyze_source_file(
        "user.js", b"export function findUser() { return 1; }\n"
    )
    target["artifact"]["relative_path"] = "src/user.js"

    project = build_project_understanding([source, target])

    assert len(project["cross_file_calls"]) == 1
    assert project["cross_file_calls"][0]["callee"] == "findUser"
    assert project["cross_file_calls"][0]["resolution"] == (
        "STATIC_JAVASCRIPT_NAMED_IMPORT"
    )
    assert project["graph"]["counts"]["edges_by_type"]["CALLS"] == 1
    assert project["claims"]["cross_file_call_languages"] == ["JavaScript"]
    assert project["claims"]["cross_file_data_flow"] == "UNRESOLVED"


def test_project_does_not_invent_javascript_call_when_binding_is_shadowed():
    source = analyze_source_file(
        "main.js",
        b'import { findUser as lookup } from "./user.js";\n'
        b'function main(lookup) { return lookup(); }\n',
    )
    source["artifact"]["relative_path"] = "src/main.js"
    target = analyze_source_file(
        "user.js", b"export function findUser() { return 1; }\n"
    )
    target["artifact"]["relative_path"] = "src/user.js"

    project = build_project_understanding([source, target])

    assert project["cross_file_calls"] == []
    assert "CALLS" not in project["graph"]["counts"]["edges_by_type"]


def test_project_requires_exported_javascript_target():
    source = analyze_source_file(
        "main.js",
        b'import { findUser } from "./user.js";\n'
        b'function main() { return findUser(); }\n',
    )
    source["artifact"]["relative_path"] = "src/main.js"
    target = analyze_source_file(
        "user.js", b"function findUser() { return 1; }\n"
    )
    target["artifact"]["relative_path"] = "src/user.js"

    project = build_project_understanding([source, target])

    assert project["cross_file_calls"] == []


def test_project_resolves_commonjs_destructured_require_call():
    source = analyze_source_file(
        "main.js",
        b'const { findUser: lookup } = require("./user.js");\n'
        b'function main() { return lookup(); }\n',
    )
    source["artifact"]["relative_path"] = "src/main.js"
    target = analyze_source_file(
        "user.js",
        b'function findUser() { return 1; }\nexports.findUser = findUser;\n',
    )
    target["artifact"]["relative_path"] = "src/user.js"

    project = build_project_understanding([source, target])

    assert project["import_relationships"][0]["status"] == "RESOLVED"
    assert project["cross_file_calls"][0]["resolution"] == (
        "STATIC_JAVASCRIPT_NAMED_IMPORT"
    )
    assert project["cross_file_calls"][0]["call_target"] == "lookup"


def test_project_graph_merges_local_security_evidence_without_dangling_edges():
    source = analyze_source_file(
        "app.py",
        b'from flask import Flask, request\napp = Flask(__name__)\n'
        b'@app.get("/item")\ndef item():\n'
        b'    return request.args.get("id")\n',
    )
    source["artifact"]["relative_path"] = "backend/app.py"

    graph = build_project_understanding([source])["graph"]
    node_ids = {node["id"] for node in graph["nodes"]}
    edge_types = {edge["type"] for edge in graph["edges"]}

    assert {"FILE", "FUNCTION", "ROUTE", "SOURCE"}.issubset(
        graph["counts"]["nodes_by_type"]
    )
    assert {"DECLARES", "HANDLED_BY", "ACCEPTS_INPUT_FROM"}.issubset(
        edge_types
    )
    assert all(
        edge["source"] in node_ids and edge["target"] in node_ids
        for edge in graph["edges"]
    )


def test_project_observes_python_source_to_cross_file_database_sink():
    route = analyze_source_file(
        "routes.py",
        b'''from flask import request
from services.users import find_user

def get_user():
    user_id = request.args.get("id")
    return find_user(user_id)
''',
    )
    route["artifact"]["relative_path"] = "app/routes.py"
    service = analyze_source_file(
        "users.py",
        b'''def find_user(user_id, cursor):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return cursor.execute(query)
''',
    )
    service["artifact"]["relative_path"] = "app/services/users.py"

    project = build_project_understanding([route, service])

    assert project["claims"]["cross_file_data_flow"] == "PARTIAL_STATIC"
    path = project["cross_file_data_flow"][0]
    assert path["source_file"] == "app/routes.py"
    assert path["target_file"] == "app/services/users.py"
    assert path["source"]["category"] == "http_query_input"
    assert path["sink"]["category"] == "sql_execution_candidate"
    assert [step["kind"] for step in path["trace"]] == [
        "SOURCE", "ASSIGNMENT", "CALL_ARGUMENT", "CALL_BOUNDARY",
        "PARAMETER", "ASSIGNMENT", "SINK",
    ]
    assert project["graph"]["counts"]["edges_by_type"][
        "CROSSES_FILE_BOUNDARY"
    ] == 1
    assert project["graph"]["counts"]["edges_by_type"]["PATH_STARTS_AT"] >= 1
    assert project["graph"]["counts"]["edges_by_type"]["PATH_ENDS_AT"] >= 1


def test_project_does_not_invent_cross_file_flow_for_unrelated_argument():
    route = analyze_source_file(
        "routes.py",
        b'''from flask import request
from services.users import find_user

def get_user():
    ignored = request.args.get("id")
    return find_user("fixed")
''',
    )
    route["artifact"]["relative_path"] = "app/routes.py"
    service = analyze_source_file(
        "users.py", b"def find_user(user_id):\n    return open(user_id).read()\n"
    )
    service["artifact"]["relative_path"] = "app/services/users.py"

    project = build_project_understanding([route, service])
    assert project["cross_file_data_flow"] == []


def test_project_observes_javascript_request_to_cross_file_filesystem_sink():
    route = analyze_source_file(
        "routes.js",
        b'import { readDocument } from "./documents.js";\n'
        b'export function download(req) { const name = req.params.name; return readDocument(name); }\n',
    )
    route["artifact"]["relative_path"] = "src/routes.js"
    service = analyze_source_file(
        "documents.js",
        b'import fs from "fs";\n'
        b'export function readDocument(name) { const path = "/srv/data/" + name; return fs.readFileSync(path); }\n',
    )
    service["artifact"]["relative_path"] = "src/documents.js"

    project = build_project_understanding([route, service])

    assert project["claims"]["cross_file_call_languages"] == ["JavaScript"]
    path = project["cross_file_data_flow"][0]
    assert path["source"]["category"] == "http_path_input"
    assert path["sink"]["category"] == "filesystem_path_operation"
