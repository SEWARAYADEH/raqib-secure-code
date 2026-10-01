"""Persistence and isolation checks for trusted evaluation data."""

import io
import json
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app.training_store import TrainingStore


TRAINING_ROOT = Path(__file__).resolve().parents[2] / "training"


def test_repository_cases_persist_with_honest_static_labels(tmp_path):
    database_path = tmp_path / "training.sqlite3"
    store = TrainingStore(str(database_path))
    assert store.sync_repository_cases(TRAINING_ROOT) == 14
    assert store.case_counts() == {
        "total": 14,
        "static_candidates": 5,
        "static_non_candidates": 8,
        "structure_only": 1,
    }
    assert store.sync_repository_cases(TRAINING_ROOT) == 14

    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            "SELECT provenance, source_text, verified_vulnerabilities, closed_findings "
            "FROM training_cases"
        ).fetchall()
    assert len(rows) == 14
    assert all(row[0] == "TRUSTED_REPOSITORY_FIXTURE" for row in rows)
    assert all(row[1] and row[2:] == (0, 0) for row in rows)

    export = tmp_path / "training_cases.jsonl"
    assert store.export_jsonl(export) == 14
    exported = [json.loads(line) for line in export.read_text(encoding="utf-8").splitlines()]
    assert len(exported) == 14
    assert {case["id"] for case in exported} == {
        row["id"] for row in json.loads(
            (TRAINING_ROOT / "cases" / "sql_injection.json").read_text(encoding="utf-8")
        )
    } | {
        row["id"] for row in json.loads(
            (TRAINING_ROOT / "cases" / "reference_fixtures.json").read_text(encoding="utf-8")
        ) if row["pack"] != "MIXED_STATIC_EVALUATION"
    }
    assert TrainingStore(str(database_path)).case_counts()["total"] == 14
    assert store.sync_repository_cases(TRAINING_ROOT, include_large_demo=True) == 15
    assert store.case_counts()["total"] == 15


def test_upload_is_not_added_to_training_corpus(tmp_path):
    training_database = tmp_path / "training.sqlite3"
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_API_TOKEN": None,
        "EMAIL_VERIFICATION_ENABLED": False,
        "AUTH_DATABASE_PATH": str(tmp_path / "auth.sqlite3"),
        "EXAMPLE_DATABASE_PATH": str(tmp_path / "examples.sqlite3"),
        "TRAINING_DATABASE_PATH": str(training_database),
    })
    unique_source = b"private_customer_function_92a70 = lambda x: x\n"
    response = app.test_client().post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(unique_source), "private.py")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    store = app.extensions["training_store"]
    assert store.case_counts()["total"] == 14
    store.export_jsonl(tmp_path / "training_cases.jsonl")
    assert unique_source not in (tmp_path / "training_cases.jsonl").read_bytes()


def test_test_run_evidence_survives_restart_without_raw_logs(tmp_path):
    database_path = tmp_path / "training.sqlite3"
    store = TrainingStore(str(database_path))
    passing_id = store.record_test_run(
        suite="backend_pytest", command_label="backend_pytest", exit_code=0,
        passed_count=3, failed_count=0, skipped_count=1,
        output="Sensitive raw test log remains outside the database.",
    )
    failing_id = store.record_test_run(
        suite="frontend_node_tests", command_label="frontend_node_tests", exit_code=1,
        passed_count=1, failed_count=1, skipped_count=0, output="Failure details",
    )
    assert store.record_test_results(passing_id, [
        ("test_alpha", "PASSED"), ("test_beta", "SKIPPED"),
    ]) == 2
    assert store.record_test_results(failing_id, [("test_gamma", "FAILED")]) == 1
    runs = {row["id"]: row for row in TrainingStore(str(database_path)).latest_test_runs()}
    assert runs[passing_id]["status"] == "PASSED"
    assert runs[passing_id]["passed_count"] == 3
    assert runs[failing_id]["status"] == "FAILED"
    assert len(runs[passing_id]["output_sha256"]) == 64
    assert TrainingStore(str(database_path)).result_counts() == {
        "total": 3, "passed": 1, "failed": 1, "skipped": 1,
    }
    assert b"Sensitive raw test log" not in database_path.read_bytes()


def test_export_cannot_leave_private_database_directory(tmp_path):
    store = TrainingStore(str(tmp_path / "private" / "training.sqlite3"))
    with pytest.raises(ValueError, match="beside its private database"):
        store.export_jsonl(tmp_path / "public.jsonl")
