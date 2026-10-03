from app.analysis_service import analyze_source_file


def test_observed_path_creates_candidate_without_vulnerability_claim():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\n\ndef run():\n    command = request.args.get("command")\n    os.system(command)\n''',
    )
    analysis = result["security_analysis"]
    candidate = analysis["candidates"][0]

    assert candidate["state"] == "CANDIDATE"
    assert candidate["reachability"]["static_path"] == "OBSERVED"
    assert candidate["reachability"]["runtime_reachability"] == "UNVERIFIED"
    assert candidate["exploitability"]["status"] == "UNVERIFIED"
    assert candidate["closure"]["status"] == "NOT_ELIGIBLE"
    assert analysis["counts"]["verified_vulnerabilities"] == 0


def test_candidate_standard_mapping_is_explicitly_unverified():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\n\ndef run():\n    command = request.args.get("command")\n    os.system(command)\n''',
    )
    standards = result["security_analysis"]["candidates"][0]["standards"]

    assert standards == {
        "cwe": "CWE-78",
        "owasp": "A03:2021-Injection",
        "status": "CANDIDATE_MAPPING",
        "basis": "os_command_execution",
    }


def test_sink_without_source_path_does_not_create_candidate():
    result = analyze_source_file(
        "task.py",
        b'''import os\n\ndef run():\n    os.system("fixed-command")\n''',
    )

    assert result["security_semantics"]["counts"]["sinks"] == 1
    assert result["security_analysis"]["candidates"] == []


def test_control_presence_never_marks_candidate_safe_or_closed():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\nimport shlex\n\ndef run():\n    command = shlex.quote(request.args.get("command"))\n    os.system(command)\n''',
    )
    candidate = result["security_analysis"]["candidates"][0]

    assert candidate["controls"]["assessment"] == "UNVERIFIED_APPLICABILITY"
    assert candidate["controls"]["effectiveness"] == "UNVERIFIED"
    assert candidate["state"] == "CANDIDATE"


def test_finding_id_is_deterministic():
    source = b'''from flask import request\nimport os\ndef run():\n    os.system(request.args.get("command"))\n'''
    first = analyze_source_file("route.py", source)
    second = analyze_source_file("route.py", source)

    assert (
        first["security_analysis"]["candidates"][0]["id"]
        == second["security_analysis"]["candidates"][0]["id"]
    )


def test_idor_pack_creates_candidate_without_runtime_claim():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request
def detail():
    object_id = request.args.get("id")
    return Document.query.get(object_id)
''',
    )
    candidate = result["security_analysis"]["candidates"][0]
    assert candidate["pack_assessment"]["pack"] == "BROKEN_AUTHORIZATION_IDOR"
    assert candidate["pack_assessment"]["status"] == (
        "OBJECT_ACCESS_WITHOUT_OBSERVED_AUTHORIZATION_CONTROL"
    )
    assert candidate["exploitability"]["status"] == "UNVERIFIED"
