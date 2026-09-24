from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
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
            "integrity": "HMAC-SHA256",
            "result": json.loads(row["result_json"]),
        }

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
