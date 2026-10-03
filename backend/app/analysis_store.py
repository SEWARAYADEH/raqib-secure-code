from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


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
        artifact_encryption_key: str,
    ) -> None:
        self.database_path = Path(database_path).resolve()
        self.integrity_key = integrity_key.encode("utf-8")
        self.artifact_encryption_key = artifact_encryption_key.encode("utf-8")
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
                    ) + (
                        len(result.get("security_analysis", {}).get("candidates", []))
                        if result.get("files") else 0
                    ),
                    "observed_paths": sum(
                        file.get("data_flow", {}).get("counts", {}).get(
                            "observed_paths", 0
                        )
                        + file.get("inter_function_data_flow", {}).get(
                            "counts", {}
                        ).get("observed_paths", 0)
                        for file in files
                    ) + result.get("project_understanding", {}).get(
                        "counts", {}
                    ).get("observed_cross_file_paths", 0),
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
        patched = proposal.get("updated_source")
        if not isinstance(patched, str):
            raise ValueError("A complete patched artifact is required.")
        artifact_bytes = patched.encode("utf-8")
        patched_sha = hashlib.sha256(artifact_bytes).hexdigest()
        if patched_sha != proposal.get("updated_sha256"):
            raise ValueError("The patched artifact digest does not match.")
        payload_json = _canonical_json(evidence)
        mac = self._repair_mac(evidence_id, analysis_id, owner_subject,
                               finding_id, created_at, payload_json)
        nonce = os.urandom(12)
        aad = _canonical_json({"evidence_id": evidence_id,
                               "analysis_id": analysis_id,
                               "owner_subject": owner_subject,
                               "finding_id": finding_id,
                               "sha256": patched_sha}).encode("utf-8")
        ciphertext = AESGCM(self._artifact_key()).encrypt(nonce, artifact_bytes, aad)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO repair_evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evidence_id, analysis_id, owner_subject, finding_id,
                 created_at, payload_json, mac),
            )
            connection.execute(
                "INSERT INTO patched_artifacts VALUES (?, ?, ?, ?)",
                (evidence_id, patched_sha, nonce, ciphertext),
            )
        return {"evidence_id": evidence_id, "analysis_id": analysis_id,
                "finding_id": finding_id, "created_at": created_at,
                "integrity": "HMAC-SHA256", "evidence": evidence,
                "patched_artifact": {"available": True, "sha256": patched_sha}}

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
        with self._connect() as connection:
            artifact = connection.execute(
                "SELECT sha256 FROM patched_artifacts WHERE evidence_id = ?",
                (row["evidence_id"],),
            ).fetchone()
        return {"evidence_id": row["evidence_id"], "analysis_id": analysis_id,
                "finding_id": finding_id, "created_at": row["created_at"],
                "integrity": "HMAC-SHA256", "evidence": json.loads(row["payload_json"]),
                "patched_artifact": {"available": artifact is not None,
                                     "sha256": artifact["sha256"] if artifact else None}}

    def get_patched_artifact(self, *, analysis_id: str, owner_subject: str,
                             finding_id: str) -> tuple[bytes, dict] | None:
        saved = self.latest_repair_evidence(analysis_id=analysis_id,
                                             owner_subject=owner_subject,
                                             finding_id=finding_id)
        if saved is None or not saved["patched_artifact"]["available"]:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM patched_artifacts WHERE evidence_id = ?",
                (saved["evidence_id"],),
            ).fetchone()
        aad = _canonical_json({"evidence_id": saved["evidence_id"],
                               "analysis_id": analysis_id,
                               "owner_subject": owner_subject,
                               "finding_id": finding_id,
                               "sha256": row["sha256"]}).encode("utf-8")
        try:
            content = AESGCM(self._artifact_key()).decrypt(
                row["nonce"], row["ciphertext"], aad,
            )
        except (InvalidTag, ValueError) as exc:
            raise AnalysisRecordIntegrityError(saved["evidence_id"]) from exc
        if (hashlib.sha256(content).hexdigest() != row["sha256"]
                or row["sha256"] != saved["evidence"].get("updated_sha256")):
            raise AnalysisRecordIntegrityError(saved["evidence_id"])
        return content, saved

    def create_verification_evidence(
        self, *, analysis_id: str, owner_subject: str, finding_id: str,
        repair_evidence_id: str, evidence: dict,
    ) -> dict:
        record = self.get(analysis_id)
        if record["owner_subject"] != owner_subject:
            raise PermissionError("The analysis belongs to another principal.")
        repair = self.latest_repair_evidence(
            analysis_id=analysis_id, owner_subject=owner_subject, finding_id=finding_id,
        )
        if repair is None or repair["evidence_id"] != repair_evidence_id:
            raise ValueError("Verification must reference the latest saved repair evidence.")
        if evidence.get("source_sha256") != record["artifact_sha256"]:
            raise ValueError("Runtime evidence does not match the immutable source digest.")
        if evidence.get("patched_sha256") != repair["patched_artifact"]["sha256"]:
            raise ValueError("Runtime evidence does not match the patched artifact digest.")
        if evidence.get("schema") != "RAQIB_RUNTIME_EVIDENCE_V1":
            raise ValueError("Runtime evidence schema is invalid.")
        for name in ("runtime_before", "functional_test", "replay_after"):
            if evidence.get(name, {}).get("status") not in {"PASS", "FAIL", "ERROR"}:
                raise ValueError(f"Runtime evidence status is invalid: {name}.")
        evidence_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        payload_json = _canonical_json(evidence)
        integrity_mac = self._repair_mac(
            evidence_id, analysis_id, owner_subject, finding_id, created_at, payload_json
        )
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO verification_evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (evidence_id, analysis_id, owner_subject, finding_id,
                 repair_evidence_id, created_at, payload_json, integrity_mac),
            )
        return {
            "evidence_id": evidence_id, "analysis_id": analysis_id,
            "finding_id": finding_id, "repair_evidence_id": repair_evidence_id,
            "created_at": created_at, "integrity": "HMAC-SHA256", "evidence": evidence,
        }

    def latest_verification_evidence(
        self, *, analysis_id: str, owner_subject: str, finding_id: str,
    ) -> dict | None:
        record = self.get(analysis_id)
        if record["owner_subject"] != owner_subject:
            raise PermissionError("The analysis belongs to another principal.")
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM verification_evidence
                WHERE analysis_id = ? AND owner_subject = ? AND finding_id = ?
                ORDER BY created_at DESC, evidence_id DESC LIMIT 1""",
                (analysis_id, owner_subject, finding_id),
            ).fetchone()
        if row is None:
            return None
        expected = self._repair_mac(
            row["evidence_id"], row["analysis_id"], row["owner_subject"],
            row["finding_id"], row["created_at"], row["payload_json"],
        )
        if not hmac.compare_digest(row["integrity_mac"], expected):
            raise AnalysisRecordIntegrityError(row["evidence_id"])
        return {
            "evidence_id": row["evidence_id"], "analysis_id": analysis_id,
            "finding_id": finding_id, "repair_evidence_id": row["repair_evidence_id"],
            "created_at": row["created_at"], "integrity": "HMAC-SHA256",
            "evidence": json.loads(row["payload_json"]),
        }

    def create_closure_record(
        self, *, analysis_id: str, owner_subject: str, finding_id: str,
        verification_evidence_id: str, closure: dict,
    ) -> dict:
        if closure.get("status") != "VERIFIED_CLOSED" or not closure.get("verified_closed"):
            raise ValueError("Only server-evaluated verified closure can be recorded.")
        verification = self.latest_verification_evidence(
            analysis_id=analysis_id, owner_subject=owner_subject, finding_id=finding_id,
        )
        if verification is None or verification["evidence_id"] != verification_evidence_id:
            raise ValueError("Closure must reference the latest verified runtime evidence.")
        analysis = self.get(analysis_id)
        findings = [
            candidate
            for file_result in (analysis["result"].get("files") or [analysis["result"]])
            for candidate in file_result.get("security_analysis", {}).get("candidates", [])
            if candidate.get("id") == finding_id
        ]
        if len(findings) != 1:
            raise ValueError("Closure finding evidence is missing or ambiguous.")
        repair = self.latest_repair_evidence(
            analysis_id=analysis_id, owner_subject=owner_subject, finding_id=finding_id,
        )
        if repair is None:
            raise ValueError("Closure requires saved repair evidence.")
        finding = findings[0]
        repair_payload = repair["evidence"]
        runtime_payload = verification["evidence"]
        record_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "analysis_id": analysis_id,
            "finding_id": finding_id,
            "verification_evidence_id": verification_evidence_id,
            "closure": closure,
            "finding": {
                "id": finding_id,
                "pack": finding.get("pack_assessment", {}).get("pack"),
                "source": finding.get("source"),
                "sink": finding.get("sink"),
                "scope": finding.get("scope"),
                "standards": finding.get("standards"),
            },
            "trace": finding.get("trace", []),
            "root_cause": repair_payload.get("root_cause"),
            "patch": {
                "original_sha256": repair_payload.get("original_sha256"),
                "patched_sha256": repair_payload.get("updated_sha256"),
                "diff": repair_payload.get("diff"),
            },
            "tests": runtime_payload.get("functional_test"),
            "verification": {
                "runtime_before": runtime_payload.get("runtime_before"),
                "replay_after": runtime_payload.get("replay_after"),
                "executor": runtime_payload.get("executor"),
            },
            "source_sha256": verification["evidence"]["source_sha256"],
            "patched_sha256": verification["evidence"]["patched_sha256"],
            "training_eligible": False,
            "training_reason": "NO_EXPLICIT_CUSTOMER_SOURCE_CONSENT",
        }
        payload_json = _canonical_json(payload)
        integrity_mac = self._repair_mac(
            record_id, analysis_id, owner_subject, finding_id, created_at, payload_json
        )
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM closure_records WHERE verification_evidence_id = ?",
                (verification_evidence_id,),
            ).fetchone()
            if existing is not None:
                return self.latest_closure_record(
                    analysis_id=analysis_id, owner_subject=owner_subject,
                    finding_id=finding_id,
                )
            connection.execute(
                """INSERT INTO closure_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (record_id, analysis_id, owner_subject, finding_id,
                 verification_evidence_id, created_at, payload_json, integrity_mac),
            )
        return {
            "record_id": record_id, "created_at": created_at,
            "integrity": "HMAC-SHA256", "record": payload,
        }

    def latest_closure_record(
        self, *, analysis_id: str, owner_subject: str, finding_id: str,
    ) -> dict | None:
        record = self.get(analysis_id)
        if record["owner_subject"] != owner_subject:
            raise PermissionError("The analysis belongs to another principal.")
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM closure_records
                WHERE analysis_id = ? AND owner_subject = ? AND finding_id = ?
                ORDER BY created_at DESC, record_id DESC LIMIT 1""",
                (analysis_id, owner_subject, finding_id),
            ).fetchone()
        if row is None:
            return None
        expected = self._repair_mac(
            row["record_id"], row["analysis_id"], row["owner_subject"],
            row["finding_id"], row["created_at"], row["payload_json"],
        )
        if not hmac.compare_digest(row["integrity_mac"], expected):
            raise AnalysisRecordIntegrityError(row["record_id"])
        return {
            "record_id": row["record_id"], "created_at": row["created_at"],
            "integrity": "HMAC-SHA256", "record": json.loads(row["payload_json"]),
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
            connection.execute(
                """CREATE TABLE IF NOT EXISTS patched_artifacts (
                    evidence_id TEXT PRIMARY KEY REFERENCES repair_evidence(evidence_id),
                    sha256 TEXT NOT NULL,
                    nonce BLOB NOT NULL,
                    ciphertext BLOB NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS verification_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL REFERENCES analysis_records(analysis_id),
                    owner_subject TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    repair_evidence_id TEXT NOT NULL REFERENCES repair_evidence(evidence_id),
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    integrity_mac TEXT NOT NULL
                )"""
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS verification_evidence_lookup ON verification_evidence "
                "(analysis_id, owner_subject, finding_id, created_at DESC)"
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS closure_records (
                    record_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL REFERENCES analysis_records(analysis_id),
                    owner_subject TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    verification_evidence_id TEXT NOT NULL UNIQUE
                        REFERENCES verification_evidence(evidence_id),
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    integrity_mac TEXT NOT NULL
                )"""
            )

    def _artifact_key(self) -> bytes:
        return hashlib.sha256(
            b"raqib-patched-artifact-v1\0" + self.artifact_encryption_key
        ).digest()

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
