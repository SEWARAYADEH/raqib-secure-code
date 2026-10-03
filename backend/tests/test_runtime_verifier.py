import hashlib
import io
import json
import subprocess
import sys

from app import create_app
from app.analysis_service import analyze_source_file
from app.repair_proposals import propose_repair
from app.runtime_verifier import OciRuntimeConfig, OciRuntimeVerifier, _HARNESS


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
    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
    )
'''


def _app(tmp_path):
    return create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "EMAIL_VERIFICATION_ENABLED": False,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "analysis.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "training.sqlite3"),
        "RECORD_INTEGRITY_KEY": "runtime-integrity-key-long-enough-12345",
        "PATCH_ARTIFACT_ENCRYPTION_KEY": "runtime-encryption-key-long-enough-12345",
    })


class PassingVerifier:
    def capability(self):
        return {"available": True, "status": "AVAILABLE"}

    def verify_repair(self, *, filename, original, patched, finding):
        assert filename == "case.py"
        assert finding["sink"]["category"] == "sql_execution_candidate"
        return {
            "schema": "RAQIB_RUNTIME_EVIDENCE_V1",
            "status": "PASS",
            "strategy": "CONTROLLED_DEPENDENCY_STUB",
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "patched_sha256": hashlib.sha256(patched).hexdigest(),
            "runtime_before": {"status": "PASS", "event_count": 1},
            "functional_test": {"status": "PASS", "scope": "TARGET_FUNCTION_SMOKE"},
            "replay_after": {"status": "PASS", "event_count": 1},
            "executor": {"engine": "test-oci", "image_id": "sha256:test"},
        }


def test_verification_api_persists_closure_without_training_source(monkeypatch, tmp_path):
    app = _app(tmp_path)
    client = app.test_client()
    created = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py")},
        content_type="multipart/form-data",
    ).get_json()
    analysis_id = created["record"]["analysis_id"]
    finding_id = created["result"]["security_analysis"]["candidates"][0]["id"]
    repair = client.post(
        f"/api/v1/analyses/{analysis_id}/repair-proposal",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py"), "finding_id": finding_id},
        content_type="multipart/form-data",
    )
    assert repair.status_code == 200
    monkeypatch.setattr("app.routes.get_runtime_verifier", lambda: PassingVerifier())
    verified = client.post(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/verify-repair",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py")},
        content_type="multipart/form-data",
    )
    assert verified.status_code == 200
    payload = verified.get_json()
    assert payload["lifecycle"]["closure"]["status"] == "VERIFIED_CLOSED"
    assert payload["closure_record"]["record"]["training_eligible"] is False
    assert payload["closure_record"]["record"]["finding"]["pack"] == "SQL_INJECTION"
    assert payload["closure_record"]["record"]["trace"]
    assert payload["closure_record"]["record"]["root_cause"]["status"] == "STATICALLY_SUPPORTED"
    assert payload["closure_record"]["record"]["patch"]["patched_sha256"]
    assert payload["closure_record"]["record"]["tests"]["status"] == "PASS"
    assert payload["closure_record"]["record"]["verification"]["replay_after"]["status"] == "PASS"
    lifecycle = client.get(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/lifecycle?file=case.py"
    ).get_json()["lifecycle"]
    assert lifecycle["runtime_before"]["status"] == "PASS"
    assert lifecycle["functional_test"]["status"] == "PASS"
    assert lifecycle["replay_after"]["status"] == "PASS"
    assert lifecycle["closure_record"]["available"] is True
    assert SQL_SOURCE not in (tmp_path / "training.sqlite3").read_bytes()


def test_verification_refuses_to_run_without_installed_runtime(tmp_path):
    app = _app(tmp_path)
    client = app.test_client()
    created = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py")},
        content_type="multipart/form-data",
    ).get_json()
    analysis_id = created["record"]["analysis_id"]
    finding_id = created["result"]["security_analysis"]["candidates"][0]["id"]
    client.post(
        f"/api/v1/analyses/{analysis_id}/repair-proposal",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py"), "finding_id": finding_id},
        content_type="multipart/form-data",
    )
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/findings/{finding_id}/verify-repair",
        data={"file": (io.BytesIO(SQL_SOURCE), "case.py")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "ISOLATION_RUNTIME_UNAVAILABLE"


def test_oci_command_enforces_isolation_and_digest_pin(monkeypatch, tmp_path):
    digest = "python:3.12-alpine@sha256:" + "a" * 64
    verifier = OciRuntimeVerifier(OciRuntimeConfig(engine="docker", image=digest))
    monkeypatch.setattr("app.runtime_verifier.shutil.which", lambda name: "/bin/docker")
    output = json.dumps({
        "schema": "RAQIB_RUNTIME_EVIDENCE_V1", "status": "PASS",
        "runtime_before": {"status": "PASS"},
        "functional_test": {"status": "PASS"},
        "replay_after": {"status": "PASS"},
    })
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[1:3] == ["image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, stdout="sha256:image\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout=output + "\n", stderr="")

    monkeypatch.setattr("app.runtime_verifier.subprocess.run", fake_run)
    result = verifier.verify_repair(
        filename="case.py", original=b"def lookup(): pass\n",
        patched=b"def lookup(): return None\n",
        finding={"scope": {"function": "lookup"},
                 "sink": {"category": "sql_execution_candidate"}},
    )
    command = calls[-1]
    assert result["status"] == "PASS"
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--user") + 1] == "65534:65534"
    assert command[command.index("--security-opt") + 1] == "no-new-privileges"
    assert command[command.index("--entrypoint") + 1] == "python"
    assert digest in command


def test_oci_capability_rejects_mutable_image_tag(monkeypatch):
    monkeypatch.setattr("app.runtime_verifier.shutil.which", lambda name: "/bin/docker")
    verifier = OciRuntimeVerifier(
        OciRuntimeConfig(engine="docker", image="python:3.12-alpine")
    )
    assert verifier.capability()["reason"] == "RUNTIME_IMAGE_NOT_DIGEST_PINNED"


def test_trusted_sql_fixture_replays_through_the_real_harness(tmp_path):
    finding = analyze_source_file("case.py", SQL_SOURCE)["security_analysis"]["candidates"][0]
    proposal = propose_repair("case.py", SQL_SOURCE, finding["id"])
    (tmp_path / "original.py").write_bytes(SQL_SOURCE)
    (tmp_path / "patched.py").write_text(proposal["updated_source"], encoding="utf-8")
    (tmp_path / "scenario.json").write_text(json.dumps({
        "category": "sql_execution_candidate", "function": "lookup",
    }), encoding="utf-8")
    (tmp_path / "runner.py").write_text(_HARNESS, encoding="utf-8")
    process = subprocess.run(
        [sys.executable, "-I", "-B", str(tmp_path / "runner.py")],
        cwd=tmp_path, capture_output=True, check=False, text=True, timeout=10,
    )
    assert process.returncode == 0, process.stderr
    evidence = json.loads(process.stdout.strip())
    assert evidence["runtime_before"]["status"] == "PASS"
    assert evidence["functional_test"]["status"] == "PASS"
    assert evidence["replay_after"]["status"] == "PASS"


def test_trusted_command_fixture_replays_through_the_real_harness(tmp_path):
    finding = analyze_source_file("case.py", COMMAND_SOURCE)["security_analysis"]["candidates"][0]
    proposal = propose_repair("case.py", COMMAND_SOURCE, finding["id"])
    (tmp_path / "original.py").write_bytes(COMMAND_SOURCE)
    (tmp_path / "patched.py").write_text(proposal["updated_source"], encoding="utf-8")
    (tmp_path / "scenario.json").write_text(json.dumps({
        "category": "process_execution", "function": "check",
    }), encoding="utf-8")
    (tmp_path / "runner.py").write_text(_HARNESS, encoding="utf-8")
    process = subprocess.run(
        [sys.executable, "-I", "-B", str(tmp_path / "runner.py")],
        cwd=tmp_path, capture_output=True, check=False, text=True, timeout=10,
    )
    assert process.returncode == 0, process.stderr
    evidence = json.loads(process.stdout.strip())
    assert evidence["runtime_before"]["status"] == "PASS"
    assert evidence["functional_test"]["status"] == "PASS"
    assert evidence["replay_after"]["status"] == "PASS"
