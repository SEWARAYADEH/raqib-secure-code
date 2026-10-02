"""Benign functional check of one pinned, checked-in synthetic SQL fixture.

This is not a sandbox or exploitability test. No uploaded source is executed.
Only the reviewed fixture function is compiled after exact-byte pinning.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request


TRUSTED_SHA256 = "7ec03e9f02f2edacd8608b01cd6142404a7b5788555268fbef7a119a470b06d4"
FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "training" / "fixtures" / "python"
    / "raqeeB_demo_5_vulnerabilities_550plus.py"
)
TEST_ID = "trusted_sql_valid_id_v1"
_OLD_QUERY = 'query = "SELECT id, username, email FROM users WHERE id = " + str(user_id)'
_NEW_QUERY = "query = 'SELECT id, username, email FROM users WHERE id = ?'"
_OLD_SINK = "        # Security sink:\n        cursor.execute(query)"
_NEW_SINK = "        # Security sink:\n        cursor.execute(query, (user_id,))"


def test_trusted_sql_normal_input(original_sha256: str, proposal: dict) -> dict:
    """Run only pinned repository bytes with a benign ID and temporary SQLite DB."""
    base = {
        "test_id": TEST_ID,
        "scope": "TRUSTED_SYNTHETIC_FIXTURE",
        "general_user_project_verification": "NOT_AVAILABLE",
        "input_category": "BENIGN_EXISTING_ID",
        "expected_result": [
            {"id": 1, "username": "Alice", "email": "alice@example.invalid"}
        ],
        "original_sha256": original_sha256,
        "patched_sha256": proposal.get("updated_sha256"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    trusted = FIXTURE.read_bytes()
    if (original_sha256 != TRUSTED_SHA256
            or hashlib.sha256(trusted).hexdigest() != TRUSTED_SHA256
            or proposal.get("original_sha256") != TRUSTED_SHA256
            or proposal.get("filename") != FIXTURE.name):
        return {**base, "status": "NOT_AVAILABLE", "reason": "NOT_PINNED_TRUSTED_FIXTURE"}
    original = trusted.decode("utf-8")
    expected_patch = (
        original.replace(_OLD_QUERY, _NEW_QUERY, 1)
        .replace(_OLD_SINK, _NEW_SINK, 1)
    )
    patched = proposal.get("updated_source", "")
    if (original.count(_OLD_QUERY) != 1 or original.count(_OLD_SINK) != 1
            or patched != expected_patch
            or hashlib.sha256(patched.encode("utf-8")).hexdigest()
            != proposal.get("updated_sha256")):
        return {**base, "status": "NOT_AVAILABLE", "reason": "PATCH_OUTSIDE_REVIEWED_FIXTURE_SHAPE"}
    try:
        with tempfile.TemporaryDirectory(prefix="raqib-trusted-sql-") as temporary:
            database = Path(temporary) / "fixture.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute(
                    "CREATE TABLE users (id INTEGER PRIMARY KEY, "
                    "username TEXT, email TEXT)"
                )
                connection.execute(
                    "INSERT INTO users VALUES (?, ?, ?)",
                    (1, "Alice", "alice@example.invalid"),
                )
                connection.commit()
            app = Flask("raqib_trusted_sql_functional")
            before = _run_function(original, app, database)
            after = _run_function(patched, app, database)
    except (SyntaxError, ValueError, sqlite3.Error, RuntimeError, KeyError, TypeError) as exc:
        return {**base, "status": "FAIL", "reason": type(exc).__name__}
    status = "PASS" if before == after == base["expected_result"] else "FAIL"
    return {
        **base, "status": status, "before_observed": before,
        "after_observed": after, "reason": "BENIGN_FUNCTIONAL_EQUIVALENCE",
    }


def _run_function(source: str, app: Flask, database: Path) -> list[dict]:
    functions = [node for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef) and node.name == "vuln_sql_injection"]
    if len(functions) != 1:
        raise ValueError("Trusted SQL function is not unique.")
    function = copy.deepcopy(functions[0])
    function.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {"sqlite3": sqlite3, "DB_PATH": database,
                 "request": request, "jsonify": jsonify}
    exec(compile(module, str(FIXTURE), "exec"), namespace)
    with app.test_request_context("/demo/sql?id=1"):
        response = namespace["vuln_sql_injection"]()
        return response.get_json()["rows"]
