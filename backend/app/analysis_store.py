from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AnalysisRecordNotFoundError(LookupError):
    pass


class AnalysisRecordIntegrityError(RuntimeError):
    pass


class AnalysisStore:
    """Append-only storage for completed analysis result records."""

    def __init__(
        self,
        database_path: str,
        integrity_key: str,
    ) -> None:
        self.database_path = Path(database_path).resolve()
        self.integrity_key = integrity_key.encode("utf-8")
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    def create(
        self,
        *,
        analysis_id: str,
        owner_subject: str,
        result: dict,
    ) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        result_json = _canonical_json(result)
        artifact_sha256 = result["artifact"]["sha256"]
        integrity_mac = self._mac(
            analysis_id=analysis_id,
            owner_subject=owner_subject,
            created_at=created_at,
            artifact_sha256=artifact_sha256,
            result_json=result_json,
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO analysis_records (
                    analysis_id,
                    owner_subject,
                    created_at,
                    artifact_sha256,
                    result_json,
                    integrity_mac
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    owner_subject,
                    created_at,
                    artifact_sha256,
                    result_json,
                    integrity_mac,
                ),
            )

        return {
            "analysis_id": analysis_id,
            "owner_subject": owner_subject,
            "created_at": created_at,
            "artifact_sha256": artifact_sha256,
            "persisted": True,
            "integrity": "HMAC-SHA256",
        }

    def get(self, analysis_id: str) -> dict:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    analysis_id,
                    owner_subject,
                    created_at,
                    artifact_sha256,
                    result_json,
                    integrity_mac
                FROM analysis_records
                WHERE analysis_id = ?
                """,
                (analysis_id,),
            ).fetchone()

        if row is None:
            raise AnalysisRecordNotFoundError(analysis_id)

        expected_mac = self._mac(
            analysis_id=row["analysis_id"],
            owner_subject=row["owner_subject"],
            created_at=row["created_at"],
            artifact_sha256=row["artifact_sha256"],
            result_json=row["result_json"],
        )

        if not hmac.compare_digest(
            row["integrity_mac"],
            expected_mac,
        ):
            raise AnalysisRecordIntegrityError(
                row["analysis_id"]
            )

        return {
            "analysis_id": row["analysis_id"],
            "owner_subject": row["owner_subject"],
            "created_at": row["created_at"],
            "artifact_sha256": row["artifact_sha256"],
            "persisted": True,
            "integrity": "HMAC-SHA256",
            "result": json.loads(row["result_json"]),
        }

    def list_for_owner(self, owner_subject: str, limit: int = 20) -> list[dict]:
        if not 1 <= limit <= 20:
            raise ValueError("Analysis list limit must be between 1 and 20.")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT analysis_id FROM analysis_records
                WHERE owner_subject = ?
                ORDER BY created_at DESC, analysis_id DESC
                LIMIT ?
                """,
                (owner_subject, limit),
            ).fetchall()

        summaries = []
        for row in rows:
            record = self.get(row["analysis_id"])
            result = record["result"]
            artifact = result.get("artifact", {})
            scope = result.get("analysis", {}).get("scope", "UNKNOWN")
            files = result.get("files") or [result]
            summaries.append(
                {
                    "analysis_id": record["analysis_id"],
                    "created_at": record["created_at"],
                    "artifact_name": artifact.get("filename", "Unknown"),
                    "scope": scope,
                    "language": result.get("language", {}).get("candidate"),
                    "project_type": result.get(
                        "project_understanding", {}
                    ).get("project_type"),
                    "files_analyzed": len(files),
                    "candidate_count": sum(
                        len(file.get("security_analysis", {}).get("candidates", []))
                        for file in files
                    ),
                    "observed_paths": sum(
                        file.get("data_flow", {}).get("counts", {}).get(
                            "observed_paths", 0
                        )
                        + file.get("inter_function_data_flow", {}).get(
                            "counts", {}
                        ).get("observed_paths", 0)
                        for file in files
                    ),
                    "integrity": record["integrity"],
                }
            )
        return summaries

    def create_repair_evidence(self, *, analysis_id: str, owner_subject: str,
                               proposal: dict) -> dict:
        record = self.get(analysis_id)
        if record["owner_subject"] != owner_subject:
            raise PermissionError("The analysis belongs to another principal.")
        finding_id = proposal["finding_id"]
        if not any(item["id"] == finding_id for item in
                   record["result"]["security_analysis"]["candidates"]):
            raise ValueError("The finding is not in the saved analysis.")
        if proposal["original_sha256"] != record["artifact_sha256"]:
            raise ValueError("The repair input does not match the saved artifact.")
        evidence_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        evidence = {key: value for key, value in proposal.items()
                    if key != "updated_source"}
        payload_json = _canonical_json(evidence)
        mac = self._repair_mac(evidence_id, analysis_id, owner_subject,
                               finding_id, created_at, payload_json)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO repair_evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evidence_id, analysis_id, owner_subject, finding_id,
                 created_at, payload_json, mac),
            )
        return {"evidence_id": evidence_id, "analysis_id": analysis_id,
                "finding_id": finding_id, "created_at": created_at,
                "integrity": "HMAC-SHA256", "evidence": evidence}

    def latest_repair_evidence(self, *, analysis_id: str, owner_subject: str,
                               finding_id: str) -> dict | None:
        record = self.get(analysis_id)
        if record["owner_subject"] != owner_subject:
            raise PermissionError("The analysis belongs to another principal.")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM repair_evidence WHERE analysis_id = ? AND owner_subject = ? "
                "AND finding_id = ? ORDER BY created_at DESC, evidence_id DESC LIMIT 1",
                (analysis_id, owner_subject, finding_id),
            ).fetchone()
        if row is None:
            return None
        expected = self._repair_mac(row["evidence_id"], row["analysis_id"],
                                    row["owner_subject"], row["finding_id"],
                                    row["created_at"], row["payload_json"])
        if not hmac.compare_digest(row["integrity_mac"], expected):
            raise AnalysisRecordIntegrityError(row["evidence_id"])
        return {"evidence_id": row["evidence_id"], "analysis_id": analysis_id,
                "finding_id": finding_id, "created_at": row["created_at"],
                "integrity": "HMAC-SHA256", "evidence": json.loads(row["payload_json"])}

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_records (
                    analysis_id TEXT PRIMARY KEY,
                    owner_subject TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    integrity_mac TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS analysis_records_owner_created
                ON analysis_records (owner_subject, created_at DESC)
                """
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS repair_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL REFERENCES analysis_records(analysis_id),
                    owner_subject TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    integrity_mac TEXT NOT NULL
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS repair_evidence_lookup ON repair_evidence "
                "(analysis_id, owner_subject, finding_id, created_at DESC)"
            )

    def _repair_mac(self, evidence_id: str, analysis_id: str, owner_subject: str,
                    finding_id: str, created_at: str, payload_json: str) -> str:
        message = _canonical_json({
            "evidence_id": evidence_id, "analysis_id": analysis_id,
            "owner_subject": owner_subject, "finding_id": finding_id,
            "created_at": created_at,
            "payload_sha256": hashlib.sha256(payload_json.encode("utf-8")).hexdigest(),
        }).encode("utf-8")
        return hmac.new(self.integrity_key, message, hashlib.sha256).hexdigest()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _mac(
        self,
        *,
        analysis_id: str,
        owner_subject: str,
        created_at: str,
        artifact_sha256: str,
        result_json: str,
    ) -> str:
        message = _canonical_json(
            {
                "analysis_id": analysis_id,
                "owner_subject": owner_subject,
                "created_at": created_at,
                "artifact_sha256": artifact_sha256,
                "result_json_sha256": hashlib.sha256(
                    result_json.encode("utf-8")
                ).hexdigest(),
            }
        ).encode("utf-8")
        return hmac.new(
            self.integrity_key,
            message,
            hashlib.sha256,
        ).hexdigest()


def _canonical_json(value: dict) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
