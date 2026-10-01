"""Real checks of trusted reference fixtures; uploaded code is never executed."""

import json
import runpy
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest
from flask import Flask

from app.analysis_service import analyze_source_file


FIXTURES = Path(__file__).resolve().parents[2] / "training" / "fixtures"
MANIFEST = Path(__file__).resolve().parents[2] / "training" / "cases" / "reference_fixtures.json"
REFERENCE_CASES = json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case", REFERENCE_CASES, ids=lambda case: case["id"],
)
def test_reference_fixtures_pass_real_parser_and_analysis(case):
    path = FIXTURES / case["path"]
    result = analyze_source_file(path.name, path.read_bytes())

    assert result["language"]["candidate"] == case["language"]
    assert result["structure"]["functions"]
    assert result["security_analysis"]["counts"]["candidates"] == case["expected_candidates"]
    assert result["security_analysis"]["counts"]["non_candidate_paths"] == case["expected_non_candidate_paths"]
    assert result["security_analysis"]["counts"]["verified_vulnerabilities"] == 0
    assert result["security_analysis"]["counts"]["closed_findings"] == 0
    if case["expected_candidates"]:
        assert result["security_analysis"]["candidates"][0]["trace"]


def test_python_sqlite_reference_fix_preserves_lookup_and_blocks_replay():
    # Only these checked-in fixtures are executed, never uploaded projects.
    unsafe = runpy.run_path(str(FIXTURES / "python/sql_lookup_unsafe.py"))
    fixed = runpy.run_path(str(FIXTURES / "python/sql_lookup_fixed.py"))
    app = Flask(__name__)
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        connection.executemany(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            [(1, "Alice"), (2, "Bob")],
        )

        with app.test_request_context("/?id=2"):
            assert unsafe["lookup_user"](connection) == ("Bob",)
            assert fixed["lookup_user"](connection) == ("Bob",)

        with app.test_request_context("/?id=999%20OR%201=1"):
            assert unsafe["lookup_user"](connection) == ("Alice",)
            assert fixed["lookup_user"](connection) is None

    rescanned = analyze_source_file(
        "sql_lookup_fixed.py",
        (FIXTURES / "python/sql_lookup_fixed.py").read_bytes(),
    )
    assert rescanned["security_analysis"]["counts"]["candidates"] == 0
    assert rescanned["security_analysis"]["non_candidates"][0][
        "assessment"
    ]["basis"] == "QUERY_TEXT_IS_STATIC_LITERAL"


def test_javascript_reference_fix_keeps_query_text_static():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for the JavaScript reference fixture")

    script = r"""
const assert = require('node:assert/strict');
const unsafe = require(process.argv[1]).lookupUser;
const fixed = require(process.argv[2]).lookupUser;
const observe = (lookup, value) => {
  const db = { query: (...args) => args };
  return lookup({ get: () => value }, db);
};
assert.deepEqual(observe(unsafe, '2'), ['SELECT name FROM users WHERE id = 2']);
assert.deepEqual(observe(fixed, '2'), ['SELECT name FROM users WHERE id = ?', ['2']]);
const payload = '999 OR 1=1';
assert.match(observe(unsafe, payload)[0], /OR 1=1/);
assert.deepEqual(observe(fixed, payload), [
  'SELECT name FROM users WHERE id = ?', [payload]
]);
console.log(JSON.stringify({ normal: 'PASS', replay: 'PARAMETER_SEPARATED' }));
"""
    process = subprocess.run(
        [
            node,
            "-e",
            script,
            str((FIXTURES / "javascript/sql_lookup_unsafe.js").resolve()),
            str((FIXTURES / "javascript/sql_lookup_fixed.js").resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert json.loads(process.stdout)["replay"] == "PARAMETER_SEPARATED"
