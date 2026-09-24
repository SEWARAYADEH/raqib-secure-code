from app.analysis_service import analyze_source_file
from app.finding_model import build_finding_candidates
from app.verification_planner import build_verification_plans


def _candidate_analysis():
    return analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\ndef run():\n    os.system(request.args.get("command"))\n''',
    )["security_analysis"]


def test_plan_is_blocked_without_isolation_runtime():
    result = build_verification_plans(
        _candidate_analysis(),
        isolation_runtime_available=False,
    )
    plan = result["plans"][0]

    assert plan["status"] == "BLOCKED"
    assert plan["execution_status"] == "NOT_RUN"
    assert plan["blockers"] == ["ISOLATION_RUNTIME_UNAVAILABLE"]
    assert result["claims"]["uploaded_code_executed"] is False
    assert result["claims"]["exploitability_verified"] is False


def test_supported_plan_is_ready_only_when_runtime_is_available():
    result = build_verification_plans(
        _candidate_analysis(),
        isolation_runtime_available=True,
    )
    plan = result["plans"][0]

    assert plan["status"] == "READY"
    assert plan["strategy"] == "INERT_SANDBOX_MARKER"
    assert plan["execution_status"] == "NOT_RUN"


def test_capability_policy_denies_host_network_files_and_secrets():
    plan = build_verification_plans(
        _candidate_analysis(),
        isolation_runtime_available=True,
    )["plans"][0]
    policy = plan["capability_policy"]

    assert policy["network"] == "DENY"
    assert policy["host_filesystem"] == "DENY"
    assert policy["host_processes"] == "DENY"
    assert policy["secrets"] == "DENY"
    assert policy["identity"] == "NON_ROOT"


def test_analysis_contract_never_marks_blocked_plan_as_executed():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\ndef run():\n    os.system(request.args.get("command"))\n''',
    )
    verification = result["exploitability_verification"]

    assert verification["counts"] == {
        "total": 1,
        "ready": 0,
        "blocked": 1,
        "executed": 0,
    }
