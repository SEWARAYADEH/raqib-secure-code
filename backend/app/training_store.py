"""Private, versioned evaluation corpus built only from checked-in fixtures."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.analysis_service import analyze_source_file


_MAX_SOURCE_BYTES = 64 * 1024
_LABELS = {"STATIC_CANDIDATE", "STATIC_NON_CANDIDATE", "NO_SECURITY_CLAIM"}


class TrainingStore:
    def __init__(self, database_path: str):
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as database:
            database.execute("""CREATE TABLE IF NOT EXISTS training_cases (
                id TEXT PRIMARY KEY,
                provenance TEXT NOT NULL CHECK (provenance = 'TRUSTED_REPOSITORY_FIXTURE'),
                pack TEXT NOT NULL,
                label TEXT NOT NULL,
                pair_id TEXT,
                role TEXT NOT NULL,
                filename TEXT NOT NULL,
                language TEXT NOT NULL,
                source_text TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                expected_candidates INTEGER NOT NULL,
                observed_candidates INTEGER NOT NULL,
                expected_non_candidate_paths INTEGER NOT NULL,
                observed_non_candidate_paths INTEGER NOT NULL,
                verified_vulnerabilities INTEGER NOT NULL CHECK (verified_vulnerabilities = 0),
                closed_findings INTEGER NOT NULL CHECK (closed_findings = 0),
                case_sha256 TEXT NOT NULL
            )""")
            database.execute("""CREATE TABLE IF NOT EXISTS training_test_runs (
                id TEXT PRIMARY KEY,
                suite TEXT NOT NULL,
                command_label TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('PASSED', 'FAILED')),
                exit_code INTEGER NOT NULL,
                passed_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                skipped_count INTEGER NOT NULL,
                output_sha256 TEXT NOT NULL,
                recorded_at_utc TEXT NOT NULL
            )""")
            database.execute("""CREATE TABLE IF NOT EXISTS training_test_results (
                run_id TEXT NOT NULL REFERENCES training_test_runs(id),
                test_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('PASSED', 'FAILED', 'SKIPPED')),
                PRIMARY KEY (run_id, test_id)
            )""")

    def sync_repository_cases(self, training_root: Path) -> int:
        """Analyze trusted versioned cases; reject label drift and altered IDs."""
        root = training_root.resolve(strict=True)
        inline = _read_manifest(root / "cases" / "sql_injection.json")
        references = _read_manifest(root / "cases" / "reference_fixtures.json")
        records = []
        for item in inline:
            source_text = item["source"]
            records.append(self._evaluate(
                case_id=item["id"], filename=item["language_file"],
                source_text=source_text, expected_candidates=item["expected_candidates"],
                expected_non_candidates=item["expected_non_candidate_paths"],
                pack="SQL_INJECTION", pair_id=None, role="EVALUATION",
            ))
        for item in references:
            fixtures_root = (root / "fixtures").resolve(strict=True)
            fixture = (fixtures_root / item["path"]).resolve(strict=True)
            if not fixture.is_relative_to(fixtures_root) or not fixture.is_file():
                raise ValueError("Reference fixture must stay inside the training directory.")
            records.append(self._evaluate(
                case_id=item["id"], filename=fixture.name,
                source_text=fixture.read_text(encoding="utf-8"),
                expected_candidates=item["expected_candidates"],
                expected_non_candidates=item["expected_non_candidate_paths"],
                pack=item["pack"], pair_id=item["pair_id"], role=item["role"],
                expected_language=item["language"], expected_label=item["label"],
            ))
        if len({record["id"] for record in records}) != len(records):
            raise ValueError("Training case IDs must be unique.")

        fields = tuple(records[0])
        with self._connect() as database:
            existing = {
                row["id"]: row for row in database.execute("SELECT * FROM training_cases")
            }
            for record in records:
                old = existing.get(record["id"])
                if old is not None:
                    if old["case_sha256"] != record["case_sha256"]:
                        raise ValueError(f"Training case changed without a new ID: {record['id']}.")
                    continue
                placeholders = ", ".join("?" for _ in fields)
                columns = ", ".join(fields)
                database.execute(
                    f"INSERT INTO training_cases ({columns}) VALUES ({placeholders})",
                    tuple(record.values()),
                )
        return len(records)

    def case_counts(self) -> dict:
        with self._connect() as database:
            row = database.execute("""SELECT COUNT(*) AS total,
                SUM(label = 'STATIC_CANDIDATE') AS static_candidates,
                SUM(label = 'STATIC_NON_CANDIDATE') AS static_non_candidates,
                SUM(label = 'NO_SECURITY_CLAIM') AS structure_only
                FROM training_cases""").fetchone()
        return {key: row[key] or 0 for key in row.keys()}

    def record_test_run(
        self, *, suite: str, command_label: str, exit_code: int,
        passed_count: int, failed_count: int, skipped_count: int, output: str,
    ) -> str:
        if not suite or not command_label or min(
            passed_count, failed_count, skipped_count
        ) < 0:
            raise ValueError("Invalid test run metadata.")
        run_id = str(uuid.uuid4())
        status = "PASSED" if exit_code == 0 and failed_count == 0 else "FAILED"
        with self._connect() as database:
            database.execute("""INSERT INTO training_test_runs VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                run_id, suite, command_label, status, exit_code,
                passed_count, failed_count, skipped_count,
                hashlib.sha256(output.encode("utf-8")).hexdigest(),
                datetime.now(timezone.utc).isoformat(),
            ))
        return run_id

    def latest_test_runs(self) -> list[dict]:
        with self._connect() as database:
            rows = database.execute("""SELECT id, suite, command_label, status,
                exit_code, passed_count, failed_count, skipped_count,
                output_sha256, recorded_at_utc FROM training_test_runs
                ORDER BY recorded_at_utc DESC LIMIT 20""").fetchall()
        return [dict(row) for row in rows]

    def record_test_results(self, run_id: str, results: list[tuple[str, str]]) -> int:
        if len({test_id for test_id, _ in results}) != len(results):
            raise ValueError("Test IDs must be unique within a run.")
        if any(not test_id or status not in {"PASSED", "FAILED", "SKIPPED"}
               for test_id, status in results):
            raise ValueError("Invalid individual test result.")
        with self._connect() as database:
            database.executemany(
                "INSERT INTO training_test_results (run_id, test_id, status) VALUES (?, ?, ?)",
                [(run_id, test_id, status) for test_id, status in results],
            )
        return len(results)

    def result_counts(self) -> dict:
        with self._connect() as database:
            row = database.execute("""SELECT COUNT(*) AS total,
                SUM(status = 'PASSED') AS passed,
                SUM(status = 'FAILED') AS failed,
                SUM(status = 'SKIPPED') AS skipped
                FROM training_test_results""").fetchone()
        return {key: row[key] or 0 for key in row.keys()}

    def export_jsonl(self, destination: Path) -> int:
        """Export only the private synthetic corpus, never user uploads."""
        target = destination.resolve()
        if target.parent != self.database_path.parent:
            raise ValueError("Training export must stay beside its private database.")
        with self._connect() as database:
            rows = database.execute("""SELECT id, provenance, pack, label,
                pair_id, role, filename, language, source_text, source_sha256,
                expected_candidates, observed_candidates,
                expected_non_candidate_paths, observed_non_candidate_paths,
                verified_vulnerabilities, closed_findings
                FROM training_cases ORDER BY id""").fetchall()
        temporary = target.with_name(f"{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as output:
                for row in rows:
                    output.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return len(rows)

    def _evaluate(
        self, *, case_id: str, filename: str, source_text: str,
        expected_candidates: int, expected_non_candidates: int,
        pack: str, pair_id: str | None, role: str,
        expected_language: str | None = None,
        expected_label: str | None = None,
    ) -> dict:
        if not isinstance(source_text, str) or not 0 < len(source_text.encode("utf-8")) <= _MAX_SOURCE_BYTES:
            raise ValueError(f"Training source is empty or too large: {case_id}.")
        result = analyze_source_file(filename, source_text.encode("utf-8"))
        language = result["language"]["candidate"]
        counts = result["security_analysis"]["counts"]
        observed = (counts["candidates"], counts["non_candidate_paths"])
        if expected_language and language != expected_language:
            raise ValueError(f"Language label changed for {case_id}.")
        if observed != (expected_candidates, expected_non_candidates):
            raise ValueError(f"Static evaluation changed for {case_id}.")
        if counts["verified_vulnerabilities"] or counts["closed_findings"]:
            raise ValueError("Static fixtures cannot prove vulnerability closure.")
        label = (
            "NO_SECURITY_CLAIM" if pack == "STRUCTURE_ONLY" else
            "STATIC_CANDIDATE" if expected_candidates else "STATIC_NON_CANDIDATE"
        )
        if label not in _LABELS:
            raise ValueError("Unsupported training label.")
        if expected_label is not None and label != expected_label:
            raise ValueError(f"Training label disagrees with static evidence for {case_id}.")
        record = {
            "id": case_id,
            "provenance": "TRUSTED_REPOSITORY_FIXTURE",
            "pack": pack,
            "label": label,
            "pair_id": pair_id,
            "role": role,
            "filename": filename,
            "language": language,
            "source_text": source_text,
            "source_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "expected_candidates": expected_candidates,
            "observed_candidates": observed[0],
            "expected_non_candidate_paths": expected_non_candidates,
            "observed_non_candidate_paths": observed[1],
            "verified_vulnerabilities": 0,
            "closed_findings": 0,
        }
        record["case_sha256"] = hashlib.sha256(json.dumps(
            record, sort_keys=True, ensure_ascii=False,
        ).encode("utf-8")).hexdigest()
        return record

    def _connect(self) -> sqlite3.Connection:
        database = sqlite3.connect(self.database_path, timeout=5)
        database.row_factory = sqlite3.Row
        database.execute("PRAGMA journal_mode = WAL")
        database.execute("PRAGMA synchronous = FULL")
        return database


def _read_manifest(path: Path) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("Training case manifest must be a list.")
    return cases
