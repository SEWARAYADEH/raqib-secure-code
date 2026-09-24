from app.analysis_service import analyze_source_file
from app.project_understanding import build_project_understanding


def _result(path: str, content: bytes) -> dict:
    result = analyze_source_file(
        path.rsplit("/", 1)[-1],
        content,
    )
    result["artifact"]["relative_path"] = path
    return result


def test_project_observes_one_boundary_python_source_to_sink_path():
    source = _result(
        "backend/app.py",
        (
            b"from flask import request\n"
            b"from services.user import find_user as lookup\n"
            b"def route():\n"
            b"    user_id = request.args.get('id')\n"
            b"    return lookup(user_id)\n"
        ),
    )
    target = _result(
        "backend/services/user.py",
        (
            b"def find_user(user_id):\n"
            b"    return database.execute(user_id)\n"
        ),
    )

    project = build_project_understanding([source, target])

    flow = project["project_data_flow"]
    assert flow["scope"] == "CROSS_FILE_ONE_BOUNDARY"
    assert flow["counts"]["observed_paths"] == 1
    assert project["counts"]["observed_cross_file_paths"] == 1
    assert (
        project["claims"]["cross_file_data_flow"]
        == "PARTIAL_STATIC_PYTHON_ONE_BOUNDARY"
    )

    path = flow["paths"][0]
    assert path["status"] == "OBSERVED"
    assert path["source_file"] == "backend/app.py"
    assert path["target_file"] == "backend/services/user.py"
    assert path["caller"] == "route"
    assert path["callee"] == "find_user"
    assert path["source"]["target"] == "request.args.get"
    assert path["sink"]["target"] == "database.execute"
    assert path["evidence_strength"] == "HEURISTIC"
    assert any(
        step["kind"] == "PROJECT_CALL_BOUNDARY"
        for step in path["trace"]
    )
    assert "vulnerability" not in path
    assert "severity" not in path
    assert "cwe" not in path


def test_project_does_not_cross_mismatched_argument_parameter_position():
    source = _result(
        "app.py",
        (
            b"from flask import request\n"
            b"from services.user import find_user\n"
            b"def route():\n"
            b"    user_id = request.args.get('id')\n"
            b"    return find_user(user_id, 'fixed')\n"
        ),
    )
    target = _result(
        "services/user.py",
        (
            b"def find_user(prefix, user_id):\n"
            b"    return database.execute(user_id)\n"
        ),
    )

    project = build_project_understanding([source, target])

    assert len(project["cross_file_calls"]) == 1
    assert project["project_data_flow"]["paths"] == []
    assert project["claims"]["cross_file_data_flow"] == "UNRESOLVED"


def test_project_flow_requires_resolved_cross_file_call():
    source = _result(
        "app.py",
        (
            b"from flask import request\n"
            b"from services.user import find_user\n"
            b"find_user = None\n"
            b"def route():\n"
            b"    value = request.args.get('id')\n"
            b"    return find_user(value)\n"
        ),
    )
    target = _result(
        "services/user.py",
        (
            b"def find_user(value):\n"
            b"    return database.execute(value)\n"
        ),
    )

    project = build_project_understanding([source, target])

    assert project["cross_file_calls"] == []
    assert project["project_data_flow"]["paths"] == []
    assert project["claims"]["cross_file_data_flow"] == "UNRESOLVED"
