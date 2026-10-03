"""Closure requires evidence; static and trusted-functional checks are insufficient."""

from copy import deepcopy

from app.analysis_service import analyze_source_file
from app.closure_evaluator import evaluate_closure
from app.repair_proposals import propose_repair


SOURCE = b'''from flask import request
import sqlite3
def lookup():
    user_id = request.args.get("id")
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    query = "SELECT id FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchall()
'''


def _evidence():
    finding = analyze_source_file("case.py", SOURCE)["security_analysis"]["candidates"][0]
    proposal = propose_repair("case.py", SOURCE, finding["id"])
    return finding, proposal


def test_static_recheck_and_patch_syntax_do_not_close():
    finding, proposal = _evidence()
    result = proposal["closure_evaluation"]
    assert result["status"] == "CLOSURE_INCOMPLETE"
    assert result["verified_closed"] is False
    gates = {item["name"]: item["status"] for item in result["gates"]}
    assert gates["PATCH_SYNTAX_VALID"] == "PASS"
    assert gates["RE_SCAN"] == "PASS"
    assert gates["RE_TRACE"] == "PASS"
    assert gates["RUNTIME_VERIFICATION_BEFORE"] == "NOT_AVAILABLE"
    assert gates["REPLAY_AFTER_PATCH"] == "NOT_AVAILABLE"
    assert finding["closure"]["status"] == "NOT_ELIGIBLE"


def test_failed_functional_check_blocks_closure():
    finding, proposal = _evidence()
    result = evaluate_closure(finding=finding, proposal=proposal,
                              functional={"status": "FAIL"})
    assert result["status"] == "NOT_CLOSED"


def test_runtime_executor_error_is_a_failed_gate_not_incomplete():
    finding, proposal = _evidence()
    result = evaluate_closure(
        finding=finding, proposal=proposal,
        functional={"status": "ERROR"},
        runtime_before={"status": "ERROR"},
        replay_after={"status": "ERROR"},
    )
    assert result["status"] == "NOT_CLOSED"
    gates = {item["name"]: item["status"] for item in result["gates"]}
    assert gates["FUNCTIONAL_TEST"] == "FAIL"
    assert gates["RUNTIME_VERIFICATION_BEFORE"] == "FAIL"
    assert gates["REPLAY_AFTER_PATCH"] == "FAIL"


def test_retrace_missing_and_forged_boolean_cannot_close():
    finding, proposal = _evidence()
    altered = deepcopy(proposal)
    altered["static_retrace"] = {"status": "UNRESOLVED", "after_paths": []}
    altered["verified_closed"] = True
    result = evaluate_closure(finding=finding, proposal=altered,
                              functional={"status": "PASS"})
    assert result["status"] == "CLOSURE_INCOMPLETE"
    assert result["verified_closed"] is False


def test_unrelated_finding_cannot_inherit_patch_evidence():
    finding, proposal = _evidence()
    altered = deepcopy(finding)
    altered["id"] = "finding:unrelated"
    result = evaluate_closure(finding=altered, proposal=proposal,
                              functional={"status": "PASS"})
    assert result["status"] == "NOT_CLOSED"
