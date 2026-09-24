import json

from app.analysis_service import analyze_source_file


SOURCE = b'''from flask import request
import os

def normalize(value):
    return value.strip()

def run():
    raw = request.args.get("command")
    command = normalize(raw)
    os.system(command)
'''


def _model() -> dict:
    return analyze_source_file(
        "example.py",
        SOURCE,
    )["application_model"]


def test_application_model_has_typed_nodes_and_edges():
    model = _model()

    assert model["counts"]["nodes_by_type"]["FILE"] == 1
    assert model["counts"]["nodes_by_type"]["FUNCTION"] == 2
    assert model["counts"]["nodes_by_type"]["SOURCE"] == 1
    assert model["counts"]["nodes_by_type"]["SINK"] == 1
    assert model["counts"]["nodes_by_type"][
        "EVIDENCE_PATH"
    ] == 1
    assert model["counts"]["edges_by_type"]["CALLS"] == 1
    assert model["counts"]["edges_by_type"][
        "PATH_STARTS_AT"
    ] == 1
    assert model["counts"]["edges_by_type"][
        "PATH_ENDS_AT"
    ] == 1


def test_application_model_ids_are_unique_and_resolved():
    model = _model()
    node_ids = {node["id"] for node in model["nodes"]}
    edge_ids = {edge["id"] for edge in model["edges"]}

    assert len(node_ids) == len(model["nodes"])
    assert len(edge_ids) == len(model["edges"])
    assert all(
        edge["source"] in node_ids
        and edge["target"] in node_ids
        for edge in model["edges"]
    )


def test_application_model_is_deterministic():
    assert _model() == _model()


def test_application_model_makes_no_vulnerability_claim():
    model = _model()
    serialized = json.dumps(model)

    assert model["claims"]["vulnerabilities_declared"] == 0
    assert '"severity"' not in serialized
    assert '"cwe"' not in serialized


def test_application_model_links_route_handler_and_unverified_auth_control():
    result = analyze_source_file(
        "route.py",
        b'''from flask import Flask\nfrom auth import login_required\napp = Flask(__name__)\n\n@app.get("/users")\n@login_required\ndef list_users():\n    return []\n''',
    )
    model = result["application_model"]

    assert result["application_understanding"]["project_role"] == "WEB_API_COMPONENT"
    assert model["counts"]["nodes_by_type"]["FRAMEWORK"] == 1
    assert model["counts"]["nodes_by_type"]["ROUTE"] == 1
    assert model["counts"]["nodes_by_type"]["AUTHENTICATION_CONTROL"] == 1
    assert model["counts"]["edges_by_type"]["HANDLED_BY"] == 1
    assert model["counts"]["edges_by_type"]["GUARDS"] == 1
    guard = next(edge for edge in model["edges"] if edge["type"] == "GUARDS")
    assert guard["evidence"]["effectiveness"] == "UNVERIFIED"


def test_route_links_only_to_security_semantics_inside_exact_handler():
    result = analyze_source_file(
        "route.py",
        b'''from flask import Flask, request\nimport os\napp = Flask(__name__)\n\n@app.post("/run")\ndef run():\n    command = request.form.get("command")\n    os.system(command)\n\ndef background():\n    os.system("fixed")\n''',
    )
    edges = result["application_model"]["edges"]

    assert sum(edge["type"] == "ACCEPTS_INPUT_FROM" for edge in edges) == 1
    assert sum(edge["type"] == "REACHES_SENSITIVE_OPERATION" for edge in edges) == 1


def test_application_model_includes_service_dependency_and_database_context():
    result = analyze_source_file(
        "repository.py",
        b'''import sqlite3\n\nclass UserService:\n    pass\n\nservice = UserService()\n\ndef find(cursor, query):\n    return cursor.execute(query)\n''',
    )
    model = result["application_model"]

    assert model["counts"]["nodes_by_type"]["DEPENDENCY_IMPORT"] == 1
    assert model["counts"]["nodes_by_type"]["SERVICE_INSTANCE"] == 1
    assert model["counts"]["nodes_by_type"]["DATABASE_OPERATION"] == 1
    assert model["counts"]["edges_by_type"]["IMPORTS_DEPENDENCY"] == 1
    assert model["counts"]["edges_by_type"]["DECLARES_SERVICE"] == 1
    database_edge = next(
        edge
        for edge in model["edges"]
        if edge["type"] == "PERFORMS_DATABASE_OPERATION"
    )
    assert database_edge["evidence"]["status"] == "CANDIDATE"
    assert database_edge["evidence"]["resource"] == "UNRESOLVED"
