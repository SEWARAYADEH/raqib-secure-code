"""Curated, reproducible examples generated from trusted synthetic cases."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from app.analysis_service import analyze_source_file


class ExampleCatalog:
    def __init__(self, database_path: str):
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evaluation_examples (
                id TEXT PRIMARY KEY,
                classification TEXT NOT NULL,
                candidate_count INTEGER NOT NULL,
                non_candidate_count INTEGER NOT NULL,
                source_sha256 TEXT NOT NULL
            )""")

    def seed_from_cases(self, cases_path: Path) -> int:
        """Add missing versioned fixtures without replacing persisted examples."""
        with self._connect() as db:
            cases = json.loads(cases_path.read_text(encoding="utf-8"))
            if not isinstance(cases, list):
                raise ValueError("Evaluation cases must be a list.")
            existing = {
                row["id"]: dict(row)
                for row in db.execute("SELECT * FROM evaluation_examples")
            }
            records = []
            for case in cases:
                source = case["source"].encode("utf-8")
                result = analyze_source_file(case["language_file"], source)
                counts = result["security_analysis"]["counts"]
                candidates = counts["candidates"]
                non_candidates = counts["non_candidate_paths"]
                if (candidates, non_candidates) != (
                    case["expected_candidates"], case["expected_non_candidate_paths"]
                ):
                    raise ValueError(f"Evaluation result changed for {case['id']}.")
                classification = "CANDIDATE" if candidates else "NOT_VERIFIED"
                record = (
                    case["id"], classification, candidates, non_candidates,
                    hashlib.sha256(source).hexdigest(),
                )
                persisted = existing.get(case["id"])
                if persisted is not None:
                    if tuple(persisted[field] for field in (
                        "id", "classification", "candidate_count",
                        "non_candidate_count", "source_sha256",
                    )) != record:
                        raise ValueError(
                            f"Versioned evaluation case changed: {case['id']}."
                        )
                    continue
                records.append(record)
            db.executemany(
                "INSERT INTO evaluation_examples VALUES (?, ?, ?, ?, ?)", records
            )
            return len(records)

    def list_examples(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, classification, candidate_count, non_candidate_count, "
                "source_sha256 FROM evaluation_examples ORDER BY id LIMIT 20"
            ).fetchall()
        return [dict(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database_path, timeout=5)
        db.row_factory = sqlite3.Row
        return db
