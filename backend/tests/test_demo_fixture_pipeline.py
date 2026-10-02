"""Exercise the controlled fixture through the ordinary upload and storage API."""

import io
from pathlib import Path

from app import create_app


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "demo"
    / "security_fixtures"
    / "raqeeB_demo_5_vulnerabilities_550plus.py"
)


def test_large_fixture_uses_real_upload_and_keeps_static_limits(tmp_path):
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "analyses.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "training.sqlite3"),
        "RECORD_INTEGRITY_KEY": "fixture-integrity-key-long-enough-12345",
    })
    client = app.test_client()
    payload = FIXTURE.read_bytes()
    response = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(payload), FIXTURE.name)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    created = response.get_json()
    assert created["record"]["persisted"] is True
    result = created["result"]
    assert result["artifact"]["line_count"] > 500
    assert result["analysis"]["execution_policy"] == "NEVER_EXECUTE_SOURCE"
    assert "source_text" not in result["artifact"]

    candidates = result["security_analysis"]["candidates"]
    by_function = {item["scope"]["function"]: item for item in candidates}
    assert "vuln_sql_injection" in by_function
    assert "vuln_command_injection" in by_function
    assert "safe_command_execution" not in by_function
    assert "safe_parameterized_sql" not in by_function
    assert all(item["state"] == "CANDIDATE" for item in candidates)
    assert result["security_analysis"]["counts"]["verified_vulnerabilities"] == 0
    assert all(not pack["can_close"] for pack in result["security_packs"])
    assert by_function["vuln_sql_injection"]["source"]["start_line"] == 164
    assert by_function["vuln_sql_injection"]["sink"]["start_line"] == 175
    assert by_function["vuln_sql_injection"]["code_evidence"]["source"]
    non_candidates = result["security_analysis"]["non_candidates"]
    assert {item["assessment"]["status"] for item in non_candidates} == {
        "NON_QUERY_ARGUMENT_ONLY", "NON_SHELL_ARGUMENT_FLOW"
    }

    analysis_id = created["record"]["analysis_id"]
    saved = client.get(f"/api/v1/analyses/{analysis_id}")
    assert saved.status_code == 200
    persisted = saved.get_json()["record"]["result"]
    assert persisted["security_analysis"]["candidates"] == candidates
    listing = client.get("/api/v1/analyses").get_json()["analyses"]
    assert listing[0]["candidate_count"] == len(candidates)
    assert payload not in (tmp_path / "training.sqlite3").read_bytes()

    proposed = client.post(
        f"/api/v1/analyses/{analysis_id}/repair-proposal",
        data={
            "file": (io.BytesIO(payload), FIXTURE.name),
            "finding_id": by_function["vuln_sql_injection"]["id"],
        },
        content_type="multipart/form-data",
    )
    assert proposed.status_code == 200
    repair = proposed.get_json()["proposal"]
    assert repair["status"] == "PROPOSED_UNVERIFIED"
    assert repair["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"
    assert repair["static_retrace"]["status"] == "OBSERVED_NON_CANDIDATE"
    assert repair["functional_test"] == "NOT_AVAILABLE"
    assert repair["functional_evidence"] == {
        "status": "NOT_AVAILABLE", "reason": "ISOLATED_EXECUTOR_UNAVAILABLE",
    }
    assert repair["root_cause"]["finding_id"] == by_function["vuln_sql_injection"]["id"]
    assert repair["root_cause"]["category"] == "SQL_TEXT_CONCATENATION"
    assert repair["root_cause"]["status"] == "STATICALLY_SUPPORTED"
    assert repair["analyzer_version"]
    assert repair["runtime_replay"] == "NOT_AVAILABLE"
    assert repair["verified_closed"] is False
    assert repair["closure_evaluation"]["status"] == "CLOSURE_INCOMPLETE"
    assert repair["updated_source"].encode("utf-8") not in (tmp_path / "training.sqlite3").read_bytes()
    evidence = client.get(
        f"/api/v1/analyses/{analysis_id}/repair-evidence/{repair['finding_id']}"
    )
    assert evidence.status_code == 200
    saved_repair = evidence.get_json()["saved_evidence"]["evidence"]
    assert saved_repair["functional_evidence"]["status"] == "NOT_AVAILABLE"
    assert saved_repair["root_cause"]["evidence"] == repair["root_cause"]["evidence"]
    gates = {gate["name"]: gate["status"] for gate in saved_repair["closure_evaluation"]["gates"]}
    assert gates["FUNCTIONAL_TEST"] == "NOT_AVAILABLE"
    assert gates["RUNTIME_VERIFICATION_BEFORE"] == "NOT_AVAILABLE"
    assert gates["REPLAY_AFTER_PATCH"] == "NOT_AVAILABLE"
    assert "updated_source" not in saved_repair
