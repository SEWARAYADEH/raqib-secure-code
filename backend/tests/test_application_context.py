from app.analysis_service import analyze_source_file


def test_local_service_instance_is_resolved_from_assignment_and_class():
    result = analyze_source_file(
        "service.py",
        b'''class UserService:\n    def find(self):\n        return None\n\nservice = UserService()\n''',
    )

    service = result["application_understanding"]["services"][0]
    assert service["variable"] == "service"
    assert service["type"] == "UserService"
    assert service["status"] == "RESOLVED"
    assert service["resolution"] == "RESOLVED_LOCAL_CLASS"


def test_imported_service_is_only_candidate():
    result = analyze_source_file(
        "app.py",
        b"from services import UserService\nservice = UserService()\n",
    )

    service = result["application_understanding"]["services"][0]
    assert service["status"] == "CANDIDATE"
    assert service["resolution"] == "CANDIDATE_IMPORTED_TYPE"


def test_database_operation_keeps_resource_unresolved():
    result = analyze_source_file(
        "repository.py",
        b'''def find(cursor, query):\n    return cursor.execute(query)\n''',
    )

    operation = result["application_understanding"]["database_operations"][0]
    assert operation["status"] == "CANDIDATE"
    assert operation["resource"] == "UNRESOLVED"


def test_permission_decorator_is_authorization_not_authentication():
    result = analyze_source_file(
        "route.py",
        b'''from flask import Flask\nfrom auth import permission_required\napp = Flask(__name__)\n@app.get("/admin")\n@permission_required("admin")\ndef admin():\n    return {}\n''',
    )

    control = result["application_understanding"]["authentication_controls"][0]
    assert control["kind"] == "AUTHORIZATION_CONTROL"
    assert control["effectiveness"] == "UNVERIFIED"


def test_dependencies_are_observed_without_origin_claim():
    result = analyze_source_file("app.py", b"import os\n")
    dependency = result["application_understanding"]["dependencies"][0]
    assert dependency["module"] == "os"
    assert dependency["status"] == "OBSERVED"
    assert dependency["origin"] == "UNRESOLVED"
