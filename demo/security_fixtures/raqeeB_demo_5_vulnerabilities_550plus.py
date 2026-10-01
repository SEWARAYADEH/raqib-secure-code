"""
RAQEEB Synthetic Security Demo
==============================

Purpose:
    A deliberately vulnerable, LOCAL-ONLY training fixture designed to exercise
    static-analysis pipelines. It contains five intentionally insecure patterns:

    1) SQL Injection candidate
    2) Command Injection candidate
    3) Path Traversal candidate
    4) Reflected XSS candidate
    5) IDOR / Broken Authorization candidate

Important:
    - This is NOT production code.
    - Do NOT deploy it to the Internet.
    - Do NOT use it against real systems.
    - It is intended only as a controlled input file for RAQEEB.
    - The file also contains safe comparison functions so the analyzer can
      distinguish insecure patterns from safer implementations.

The vulnerable functions are clearly marked with VULN_* comments.
"""

from __future__ import annotations

import html
import json
import os
import shlex
import sqlite3
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Flask is imported because RAQEEB's current Python analysis is intended to
# understand web-input sources such as request.args / request.form.
try:
    from flask import Flask, request, jsonify, render_template_string, abort
except Exception:
    # Keep the file importable in environments where Flask is not installed.
    class _DummyRequest:
        args: Dict[str, str] = {}
        form: Dict[str, str] = {}
        headers: Dict[str, str] = {}

    request = _DummyRequest()

    class Flask:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def route(self, *args: Any, **kwargs: Any):
            def decorator(func):
                return func
            return decorator

    def jsonify(value: Any) -> Any:
        return value

    def render_template_string(template: str, **kwargs: Any) -> str:
        return template

    def abort(code: int) -> None:
        raise RuntimeError(f"abort({code})")


APP_ROOT = Path(__file__).resolve().parent
UPLOAD_ROOT = APP_ROOT / "demo_uploads"
DB_PATH = APP_ROOT / "raqeeB_demo.sqlite3"

app = Flask(__name__)


@dataclass
class User:
    id: int
    username: str
    role: str


@dataclass
class Document:
    id: int
    owner_id: int
    title: str
    body: str


@dataclass
class AnalysisNote:
    category: str
    message: str
    severity: str


DEMO_USERS: Dict[int, User] = {
    1: User(id=1, username="alice", role="user"),
    2: User(id=2, username="bob", role="user"),
    99: User(id=99, username="admin", role="admin"),
}

DEMO_DOCUMENTS: Dict[int, Document] = {
    101: Document(id=101, owner_id=1, title="Alice Plan", body="private demo text"),
    102: Document(id=102, owner_id=2, title="Bob Plan", body="private demo text"),
    199: Document(id=199, owner_id=99, title="Admin Note", body="private demo text"),
}


def init_demo_db() -> None:
    """Create a small local database used only by this synthetic fixture."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO users(id, username, email) VALUES (?, ?, ?)",
            (1, "alice", "alice@example.invalid"),
        )
        conn.execute(
            "INSERT OR IGNORE INTO users(id, username, email) VALUES (?, ?, ?)",
            (2, "bob", "bob@example.invalid"),
        )
        conn.commit()
    finally:
        conn.close()


def current_demo_user() -> User:
    """
    Return a deterministic local demo user.
    In a real app this would come from authenticated session state.
    """
    return DEMO_USERS[1]


# ---------------------------------------------------------------------------
# 1) SQL INJECTION CANDIDATE
# ---------------------------------------------------------------------------

@app.route("/demo/sql")
def vuln_sql_injection():
    """
    VULN_SQL_INJECTION

    Source:
        request.args.get("id")

    Sink:
        cursor.execute(query)

    Weakness:
        User-controlled data is concatenated directly into an SQL statement.
    """
    user_id = request.args.get("id", "1")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()

        # VULN_SQL_INJECTION:
        query = "SELECT id, username, email FROM users WHERE id = " + str(user_id)

        # Security sink:
        cursor.execute(query)

        rows = [dict(row) for row in cursor.fetchall()]
        return jsonify({"rows": rows, "query": query})
    finally:
        conn.close()


@app.route("/demo/sql-safe")
def safe_parameterized_sql():
    """
    SAFE_REFERENCE_SQL

    This is intentionally safer than vuln_sql_injection:
    parameter binding is used instead of concatenating user input.
    """
    user_id = request.args.get("id", "1")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()

        # Safe parameter binding.
        cursor.execute(
            "SELECT id, username, email FROM users WHERE id = ?",
            (user_id,),
        )

        rows = [dict(row) for row in cursor.fetchall()]
        return jsonify({"rows": rows})
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 2) COMMAND INJECTION CANDIDATE
# ---------------------------------------------------------------------------

@app.route("/demo/command")
def vuln_command_injection():
    """
    VULN_COMMAND_INJECTION

    Source:
        request.args.get("host")

    Sink:
        subprocess.run(..., shell=True)

    Weakness:
        User-controlled input becomes part of a shell command string.
    """
    host = request.args.get("host", "localhost")

    # VULN_COMMAND_INJECTION:
    command = "echo Checking host: " + str(host)

    # Security sink. Deliberately insecure for static-analysis demo only.
    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=2,
    )

    return jsonify(
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[:200],
        }
    )


@app.route("/demo/command-safe")
def safe_command_execution():
    """
    SAFE_REFERENCE_COMMAND

    shell=False and a fixed executable/argument list avoid handing an
    attacker-controlled string to the shell.
    """
    host = request.args.get("host", "localhost")

    completed = subprocess.run(
        ["echo", "Checking host:", str(host)],
        shell=False,
        capture_output=True,
        text=True,
        timeout=2,
    )

    return jsonify(
        {
            "returncode": completed.returncode,
            "stdout": completed.stdout[:200],
        }
    )


# ---------------------------------------------------------------------------
# 3) PATH TRAVERSAL CANDIDATE
# ---------------------------------------------------------------------------

@app.route("/demo/file")
def vuln_path_traversal():
    """
    VULN_PATH_TRAVERSAL

    Source:
        request.args.get("name")

    Sink:
        open(...)

    Weakness:
        A user-controlled path component is joined and opened without proving
        that the final resolved path remains inside the allowed base directory.
    """
    filename = request.args.get("name", "example.txt")

    # VULN_PATH_TRAVERSAL:
    target = UPLOAD_ROOT / str(filename)

    with open(target, "r", encoding="utf-8", errors="replace") as handle:
        content = handle.read(500)

    return jsonify({"name": filename, "content": content})


@app.route("/demo/file-safe")
def safe_file_access():
    """
    SAFE_REFERENCE_PATH

    Resolve the path and verify it remains inside UPLOAD_ROOT.
    """
    filename = request.args.get("name", "example.txt")
    base = UPLOAD_ROOT.resolve()
    candidate = (base / str(filename)).resolve()

    if base not in candidate.parents and candidate != base:
        abort(400)

    with open(candidate, "r", encoding="utf-8", errors="replace") as handle:
        content = handle.read(500)

    return jsonify({"name": candidate.name, "content": content})


# ---------------------------------------------------------------------------
# 4) REFLECTED XSS CANDIDATE
# ---------------------------------------------------------------------------

@app.route("/demo/xss")
def vuln_reflected_xss():
    """
    VULN_REFLECTED_XSS

    Source:
        request.args.get("name")

    Sink:
        render_template_string(template)

    Weakness:
        User-controlled input is concatenated into HTML/template source before
        rendering.

    Note:
        RAQEEB's current proposal states that XSS analysis is not yet a complete
        implemented security pack. If the analyzer does not flag this case,
        that result must be reported honestly as unsupported/not detected.
    """
    name = request.args.get("name", "visitor")

    # VULN_REFLECTED_XSS:
    template = "<html><body><h1>Hello " + str(name) + "</h1></body></html>"

    # Security-sensitive sink:
    return render_template_string(template)


@app.route("/demo/xss-safe")
def safe_reflected_output():
    """
    SAFE_REFERENCE_XSS

    Demonstrates explicit escaping before interpolation for this synthetic file.
    """
    name = request.args.get("name", "visitor")
    escaped = html.escape(str(name), quote=True)

    template = "<html><body><h1>Hello " + escaped + "</h1></body></html>"
    return render_template_string(template)


# ---------------------------------------------------------------------------
# 5) IDOR / BROKEN AUTHORIZATION CANDIDATE
# ---------------------------------------------------------------------------

@app.route("/demo/document/<int:doc_id>")
def vuln_idor(doc_id: int):
    """
    VULN_IDOR

    Source:
        Route parameter doc_id

    Sensitive object:
        DEMO_DOCUMENTS[doc_id]

    Weakness:
        The object is returned by identifier without verifying that the
        authenticated user owns it or has an authorized role.

    Note:
        RAQEEB's current proposal states that IDOR/Broken Authorization is not
        yet implemented as a complete analysis pack. The demo should preserve
        that limitation instead of fabricating a finding.
    """
    document = DEMO_DOCUMENTS.get(doc_id)
    if document is None:
        abort(404)

    # VULN_IDOR:
    # Missing ownership/authorization check.
    return jsonify(asdict(document))


@app.route("/demo/document-safe/<int:doc_id>")
def safe_document_access(doc_id: int):
    """
    SAFE_REFERENCE_IDOR

    Verify object ownership (or admin privilege) before returning the document.
    """
    user = current_demo_user()
    document = DEMO_DOCUMENTS.get(doc_id)

    if document is None:
        abort(404)

    if document.owner_id != user.id and user.role != "admin":
        abort(403)

    return jsonify(asdict(document))


# ---------------------------------------------------------------------------
# DEMO METADATA / EXPECTED STATIC-ANALYSIS INTENT
# ---------------------------------------------------------------------------

EXPECTED_CASES: List[AnalysisNote] = [
    AnalysisNote(
        category="SQL Injection",
        message="Expected to be detectable by RAQEEB's current partial static SQL analysis.",
        severity="candidate",
    ),
    AnalysisNote(
        category="Command Injection",
        message="Expected to be detectable by RAQEEB's current partial static command analysis.",
        severity="candidate",
    ),
    AnalysisNote(
        category="Path Traversal",
        message="Present in fixture, but current project proposal says the pack is not implemented yet.",
        severity="unsupported-currently",
    ),
    AnalysisNote(
        category="XSS",
        message="Present in fixture, but current project proposal says XSS pack is not implemented yet.",
        severity="unsupported-currently",
    ),
    AnalysisNote(
        category="IDOR",
        message="Present in fixture, but current project proposal says IDOR pack is not implemented yet.",
        severity="unsupported-currently",
    ),
]


def fixture_manifest() -> Dict[str, Any]:
    """Return non-security metadata describing the controlled fixture."""
    return {
        "name": "RAQEEB 5-category synthetic fixture",
        "local_only": True,
        "intentionally_vulnerable": True,
        "categories": [asdict(item) for item in EXPECTED_CASES],
    }


def manifest_json() -> str:
    return json.dumps(fixture_manifest(), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# SUPPORT UTILITIES
# These are harmless functions included to make the fixture large enough to
# resemble a non-trivial source file and to exercise structural parsing.
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    return " ".join(str(value).strip().split())


def clamp_integer(value: Any, minimum: int, maximum: int, default: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def chunk_items(items: Iterable[Any], size: int = 10) -> List[List[Any]]:
    bucket: List[List[Any]] = []
    current: List[Any] = []
    for item in items:
        current.append(item)
        if len(current) >= size:
            bucket.append(current)
            current = []
    if current:
        bucket.append(current)
    return bucket


def stable_label(prefix: str, number: int) -> str:
    return f"{prefix}-{number:04d}"


def summarize_mapping(data: Dict[str, Any]) -> Dict[str, str]:
    return {str(key): normalize_text(value)[:120] for key, value in data.items()}



def helper_001(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 001; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "001"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_002(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 002; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "002"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_003(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 003; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "003"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_004(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 004; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "004"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_005(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 005; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "005"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_006(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 006; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "006"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_007(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 007; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "007"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_008(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 008; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "008"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_009(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 009; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "009"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_010(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 010; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "010"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_011(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 011; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "011"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_012(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 012; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "012"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_013(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 013; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "013"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_014(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 014; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "014"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_015(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 015; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "015"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_016(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 016; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "016"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_017(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 017; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "017"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_018(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 018; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "018"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_019(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 019; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "019"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_020(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 020; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "020"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_021(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 021; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "021"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_022(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 022; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "022"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_023(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 023; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "023"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_024(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 024; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "024"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_025(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 025; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "025"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_026(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 026; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "026"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_027(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 027; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "027"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_028(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 028; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "028"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_029(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 029; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "029"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_030(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 030; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "030"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_031(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 031; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "031"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_032(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 032; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "032"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_033(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 033; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "033"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_034(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 034; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "034"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_035(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 035; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "035"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_036(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 036; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "036"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_037(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 037; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "037"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_038(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 038; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "038"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_039(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 039; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "039"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_040(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 040; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "040"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_041(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 041; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "041"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_042(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 042; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "042"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_043(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 043; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "043"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_044(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 044; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "044"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_045(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 045; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "045"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_046(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 046; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "046"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_047(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 047; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "047"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_048(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 048; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "048"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_049(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 049; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "049"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_050(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 050; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "050"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_051(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 051; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "051"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_052(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 052; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "052"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_053(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 053; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "053"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_054(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 054; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "054"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_055(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 055; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "055"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_056(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 056; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "056"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_057(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 057; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "057"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_058(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 058; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "058"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_059(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 059; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "059"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_060(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 060; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "060"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_061(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 061; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "061"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_062(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 062; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "062"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_063(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 063; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "063"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_064(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 064; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "064"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_065(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 065; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "065"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_066(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 066; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "066"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_067(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 067; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "067"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_068(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 068; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "068"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_069(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 069; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "069"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_070(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 070; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "070"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_071(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 071; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "071"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_072(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 072; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "072"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_073(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 073; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "073"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_074(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 074; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "074"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_075(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 075; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "075"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_076(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 076; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "076"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_077(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 077; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "077"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_078(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 078; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "078"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_079(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 079; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "079"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_080(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 080; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "080"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_081(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 081; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "081"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_082(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 082; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "082"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_083(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 083; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "083"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_084(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 084; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "084"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_085(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 085; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "085"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_086(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 086; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "086"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_087(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 087; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "087"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_088(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 088; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "088"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_089(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 089; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "089"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata

def helper_090(value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Harmless structural helper 090; unrelated to the vulnerable sinks."""
    metadata = dict(metadata or {})
    text = normalize_text(value)
    metadata["helper"] = "090"
    metadata["length"] = len(text)
    metadata["empty"] = (text == "")
    metadata["preview"] = text[:40]
    return metadata


# ---------------------------------------------------------------------------
# SIMPLE LOCAL SETUP
# ---------------------------------------------------------------------------

def prepare_local_demo_files() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    sample = UPLOAD_ROOT / "example.txt"
    if not sample.exists():
        sample.write_text(
            "This is a controlled local file used by the RAQEEB demo fixture.\n",
            encoding="utf-8",
        )


def print_demo_summary() -> None:
    print("=" * 72)
    print("RAQEEB SYNTHETIC SECURITY FIXTURE")
    print("=" * 72)
    print("This file is intentionally vulnerable and must remain local-only.")
    print()
    print("Included categories:")
    for index, item in enumerate(EXPECTED_CASES, start=1):
        print(f"{index}. {item.category}: {item.severity}")
    print()
    print("Expected current-project behavior:")
    print("- SQL Injection: partial static candidate support")
    print("- Command Injection: partial static candidate support")
    print("- Path Traversal: fixture present; pack currently not implemented")
    print("- XSS: fixture present; pack currently not implemented")
    print("- IDOR: fixture present; pack currently not implemented")
    print()
    print("Do not convert unsupported categories into fake findings.")
    print("=" * 72)


if __name__ == "__main__":
    prepare_local_demo_files()
    init_demo_db()
    print_demo_summary()

    # Do NOT automatically expose the intentionally vulnerable fixture on a
    # network interface. Run it only inside a controlled local environment if
    # you specifically need to exercise the web routes.
    #
    # Example for a controlled localhost-only demo:
    # app.run(host="127.0.0.1", port=5055, debug=False)
