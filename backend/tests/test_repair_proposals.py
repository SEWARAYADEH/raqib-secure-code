import io
import hashlib
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


PATH_SOURCE = b'''from flask import request, abort
from pathlib import Path

UPLOAD_ROOT = Path("/srv/data")

def download():
    filename = request.args.get("name")
    target = UPLOAD_ROOT / str(filename)
    with open(target, "r", encoding="utf-8") as handle:
        return handle.read()
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
    assert proposal["functional_test"] == "NOT_AVAILABLE"
    assert proposal["functional_evidence"]["status"] == "NOT_AVAILABLE"
    assert proposal["verified_closed"] is False
    assert proposal["closure_evaluation"]["status"] == "CLOSURE_INCOMPLETE"
    assert b"cursor.execute(query)" in SQL_SOURCE


@pytest.mark.parametrize(
    "expression",
    [
        'f"SELECT id FROM users WHERE id = {user_id}"',
        '"SELECT id FROM users WHERE id = %s" % user_id',
        '"SELECT id FROM users WHERE id = {}".format(user_id)',
    ],
)
def test_sql_proposal_supports_reviewed_single_value_constructions(expression):
    source = SQL_SOURCE.replace(
        b'"SELECT id FROM users WHERE id = " + str(user_id)', expression.encode()
    )
    proposal = propose_repair("case.py", source, _finding(source)["id"])
    assert "query = 'SELECT id FROM users WHERE id = ?'" in proposal["updated_source"]
    assert "cursor.execute(query, (user_id,))" in proposal["updated_source"]
    assert proposal["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"


def test_command_proposal_uses_argument_list_and_disables_shell():
    proposal = propose_repair("case.py", COMMAND_SOURCE, _finding(COMMAND_SOURCE)["id"])
    assert "['echo', 'Checking', 'host:', str(host)]" in proposal["updated_source"]
    assert "shell=False" in proposal["updated_source"]
    assert proposal["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"
    assert proposal["static_retrace"]["status"] == "OBSERVED_NON_CANDIDATE"
    assert proposal["runtime_replay"] == "NOT_AVAILABLE"


def test_unreviewed_shell_shape_is_not_patched():
    source = COMMAND_SOURCE.replace(b"echo Checking host: ", b"sh -c ")
    with pytest.raises(RepairNotAvailable):
        propose_repair("case.py", source, _finding(source)["id"])


def test_path_proposal_resolves_and_rejects_escape_without_overwriting_original():
    finding = _finding(PATH_SOURCE)
    proposal = propose_repair("case.py", PATH_SOURCE, finding["id"])
    assert "raqib_allowed_root = UPLOAD_ROOT.resolve()" in proposal["updated_source"]
    assert "target = (UPLOAD_ROOT / str(filename)).resolve()" in proposal["updated_source"]
    assert "raqib_allowed_root not in target.parents" in proposal["updated_source"]
    assert "abort(400)" in proposal["updated_source"]
    assert proposal["static_reanalysis"]["status"] == "NO_MATCH_OBSERVED"
    assert proposal["static_retrace"]["status"] == "OBSERVED_NON_CANDIDATE"
    assert proposal["root_cause"]["category"] == "UNCONTAINED_USER_PATH"
    assert proposal["runtime_replay"] == "NOT_AVAILABLE"
    assert b"raqib_allowed_root" not in PATH_SOURCE


def test_path_proposal_refuses_to_invent_an_error_contract():
    source = PATH_SOURCE.replace(b"request, abort", b"request")
    with pytest.raises(RepairNotAvailable, match="abort import"):
        propose_repair("case.py", source, _finding(source)["id"])


def test_command_lifecycle_persists_a_separate_downloadable_patch(tmp_path):
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "command-analysis.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "command-training.sqlite3"),
        "RECORD_INTEGRITY_KEY": "command-integrity-key-long-enough-12345",
        "PATCH_ARTIFACT_ENCRYPTION_KEY": "command-encryption-key-long-enough-98765",
    })
    client = app.test_client()
    uploaded = client.post("/api/v1/analysis/source", data={
        "file": (io.BytesIO(COMMAND_SOURCE), "command_case.py")
    }, content_type="multipart/form-data").get_json()
    analysis_id = uploaded["record"]["analysis_id"]
    finding_id = uploaded["result"]["security_analysis"]["candidates"][0]["id"]
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/repair-proposal",
        data={"file": (io.BytesIO(COMMAND_SOURCE), "command_case.py"),
              "finding_id": finding_id},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    lifecycle_url = (
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/lifecycle"
        "?file=command_case.py"
    )
    lifecycle = client.get(lifecycle_url).get_json()["lifecycle"]
    assert lifecycle["patch"]["status"] == "PROPOSED_UNVERIFIED"
    assert lifecycle["closure"]["status"] == "CLOSURE_INCOMPLETE"
    patched = client.get(lifecycle_url + "&download=patched")
    assert patched.status_code == 200
    assert b"shell=False" in patched.data
    assert b"['echo', 'Checking', 'host:', str(host)]" in patched.data
    assert COMMAND_SOURCE != patched.data


def test_repair_api_requires_exact_original_and_returns_real_patch(tmp_path):
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "analysis.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "training.sqlite3"),
        "RECORD_INTEGRITY_KEY": "repair-integrity-key-long-enough-12345",
        "PATCH_ARTIFACT_ENCRYPTION_KEY": "repair-encryption-key-long-enough-67890",
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
    lifecycle_url = f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/lifecycle?file=case.py"
    lifecycle_response = client.get(lifecycle_url)
    assert lifecycle_response.status_code == 200
    lifecycle = lifecycle_response.get_json()["lifecycle"]
    stages = {stage["id"]: stage["status"] for stage in lifecycle["stages"]}
    assert stages["UNDERSTAND"] == "OBSERVED"
    assert stages["TRACE"] == "OBSERVED"
    assert stages["VERIFY"] == "NOT_AVAILABLE"
    assert stages["PATCH"] == "PROPOSED_UNVERIFIED"
    assert stages["FUNCTIONAL_TEST"] == "NOT_AVAILABLE"
    assert stages["REPLAY"] == "NOT_AVAILABLE"
    assert stages["RE_SCAN_RE_TRACE"] == "PASS"
    assert stages["CLOSURE"] == "CLOSURE_INCOMPLETE"
    patched = client.get(lifecycle_url + "&download=patched")
    assert patched.status_code == 200
    assert patched.data == proposal["updated_source"].encode("utf-8")
    assert hashlib.sha256(patched.data).hexdigest() == lifecycle["patch"]["sha256"]
    assert b"cursor.execute(query, (user_id,))" in patched.data
    assert b"# cursor.execute(query)" not in patched.data
    report = client.get(lifecycle_url + "&download=report")
    assert report.status_code == 200
    assert report.get_json()["lifecycle"]["closure"]["status"] == "CLOSURE_INCOMPLETE"
    assert b"updated_source" not in report.data
    with sqlite3.connect(tmp_path / "analysis.sqlite3") as database:
        encrypted = database.execute(
            "SELECT ciphertext FROM patched_artifacts"
        ).fetchone()[0]
        assert proposal["updated_source"].encode("utf-8") not in encrypted
        database.execute(
            "UPDATE patched_artifacts SET ciphertext = ?",
            (bytes([encrypted[0] ^ 1]) + encrypted[1:],),
        )
    assert client.get(lifecycle_url + "&download=patched").status_code == 500
    with sqlite3.connect(tmp_path / "analysis.sqlite3") as database:
        database.execute("UPDATE patched_artifacts SET ciphertext = ?", (encrypted,))
    assert client.get(lifecycle_url + "&download=patched").status_code == 200
    app.config.update(
        ANALYSIS_LOCAL_ONLY=False,
        ANALYSIS_API_TOKEN="different-owner-token-long-enough-12345",
        ANALYSIS_TOKEN_SUBJECT="another-owner",
    )
    other_headers = {
        "Authorization": "Bearer different-owner-token-long-enough-12345"
    }
    assert client.get(lifecycle_url, headers=other_headers).status_code == 403
    assert client.get(
        lifecycle_url + "&download=patched", headers=other_headers
    ).status_code == 403
    app.config["ANALYSIS_LOCAL_ONLY"] = True
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
