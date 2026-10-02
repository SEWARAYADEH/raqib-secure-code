import io
import sqlite3

import pytest

from app import create_app
from app.analysis_service import analyze_source_file
from app.repair_proposals import RepairNotAvailable, propose_repair


SQL_SOURCE = b'''from flask import request
import sqlite3

def lookup():
    user_id = request.args.get("id")
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    query = "SELECT id FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchall()
'''


COMMAND_SOURCE = b'''from flask import request
import subprocess

def check():
    host = request.args.get("host")
    command = "echo Checking host: " + str(host)
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
    )
    return result
'''


def _finding(source: bytes):
    return analyze_source_file("case.py", source)["security_analysis"]["candidates"][0]


def test_sql_proposal_changes_two_lines_and_remains_unverified():
    proposal = propose_repair("case.py", SQL_SOURCE, _finding(SQL_SOURCE)["id"])
    assert proposal["diff"].count("@@") == 2
    assert "cursor.execute(query, (user_id,))" in proposal["updated_source"]
    assert proposal["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"
    assert proposal["static_retrace"]["status"] == "OBSERVED_NON_CANDIDATE"
    assert proposal["static_retrace"]["before_trace"]
    assert proposal["static_retrace"]["after_paths"][0]["assessment"]["basis"] == "INPUT_ONLY_IN_LATER_ARGUMENT"
    assert proposal["functional_test"] == "NOT_RUN"
    assert proposal["verified_closed"] is False
    assert proposal["closure_evaluation"]["status"] == "CLOSURE_INCOMPLETE"
    assert b"cursor.execute(query)" in SQL_SOURCE


def test_command_proposal_uses_argument_list_and_disables_shell():
    proposal = propose_repair("case.py", COMMAND_SOURCE, _finding(COMMAND_SOURCE)["id"])
    assert "['echo', 'Checking', 'host:', str(host)]" in proposal["updated_source"]
    assert "shell=False" in proposal["updated_source"]
    assert proposal["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"
    assert proposal["static_retrace"]["status"] == "OBSERVED_NON_CANDIDATE"
    assert proposal["runtime_replay"] == "NOT_RUN"


def test_unreviewed_shell_shape_is_not_patched():
    source = COMMAND_SOURCE.replace(b"echo Checking host: ", b"sh -c ")
    with pytest.raises(RepairNotAvailable):
        propose_repair("case.py", source, _finding(source)["id"])


def test_repair_api_requires_exact_original_and_returns_real_patch(tmp_path):
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "analysis.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "training.sqlite3"),
        "RECORD_INTEGRITY_KEY": "repair-integrity-key-long-enough-12345",
    })
    client = app.test_client()
    uploaded = client.post("/api/v1/analysis/source", data={
        "file": (io.BytesIO(SQL_SOURCE), "case.py")
    }, content_type="multipart/form-data").get_json()
    analysis_id = uploaded["record"]["analysis_id"]
    finding_id = uploaded["result"]["security_analysis"]["candidates"][0]["id"]
    url = f"/api/v1/analyses/{analysis_id}/repair-proposal"
    mismatch = client.post(url, data={
        "file": (io.BytesIO(SQL_SOURCE + b"\n"), "case.py"), "finding_id": finding_id,
    }, content_type="multipart/form-data")
    assert mismatch.status_code == 409
    response = client.post(url, data={
        "file": (io.BytesIO(SQL_SOURCE), "case.py"), "finding_id": finding_id,
        "verified_closed": "true",
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    proposal = response.get_json()["proposal"]
    assert proposal["status"] == "PROPOSED_UNVERIFIED"
    assert proposal["original_sha256"] == uploaded["result"]["artifact"]["sha256"]
    assert proposal["verified_closed"] is False
    assert proposal["closure_evaluation"]["verified_closed"] is False
    stored = client.get(f"/api/v1/analyses/{analysis_id}/repair-evidence/{finding_id}")
    assert stored.status_code == 200
    assert stored.get_json()["saved_evidence"]["evidence"]["closure_evaluation"]["verified_closed"] is False
    assert "updated_source" not in stored.get_json()["saved_evidence"]["evidence"]
    with pytest.raises(PermissionError):
        app.extensions["analysis_store"].latest_repair_evidence(
            analysis_id=analysis_id, owner_subject="another-owner",
            finding_id=finding_id,
        )

    oversized = client.post(url, data={
        "file": (io.BytesIO(SQL_SOURCE + b" " * (256 * 1024)), "case.py"),
        "finding_id": finding_id,
    }, content_type="multipart/form-data")
    assert oversized.status_code == 413

    with sqlite3.connect(tmp_path / "analysis.sqlite3") as database:
        database.execute(
            "UPDATE repair_evidence SET payload_json = ? WHERE analysis_id = ?",
            ('{"verified_closed":true}', analysis_id),
        )
    tampered = client.get(f"/api/v1/analyses/{analysis_id}/repair-evidence/{finding_id}")
    assert tampered.status_code == 500
