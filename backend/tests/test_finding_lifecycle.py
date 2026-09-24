import pytest

from app.finding_lifecycle import (
    Evidence,
    InvalidFindingTransition,
    transition_finding,
)


def _finding(state="CANDIDATE"):
    return {
        "id": "finding:one",
        "state": state,
        "closure": {"status": "NOT_ELIGIBLE", "evidence": []},
    }


def test_candidate_cannot_skip_to_closed():
    with pytest.raises(InvalidFindingTransition):
        transition_finding(_finding(), "CLOSED", [])


def test_candidate_requires_exploitability_proof_to_be_verified():
    with pytest.raises(InvalidFindingTransition):
        transition_finding(_finding(), "VERIFIED", [])

    verified = transition_finding(
        _finding(),
        "VERIFIED",
        [Evidence("EXPLOITABILITY_PROOF", "PASSED", "replay:1")],
    )
    assert verified["state"] == "VERIFIED"


def test_closure_requires_all_five_successful_evidence_types():
    finding = _finding("FIX_APPLIED_UNVERIFIED")
    incomplete = [
        Evidence("FUNCTIONAL_TEST", "PASSED", "test:1"),
        Evidence("REPLAY", "PASSED", "replay:2"),
    ]
    with pytest.raises(InvalidFindingTransition):
        transition_finding(finding, "CLOSED", incomplete)

    evidence = [
        Evidence("FUNCTIONAL_TEST", "PASSED", "test:1"),
        Evidence("REPLAY", "PASSED", "replay:2"),
        Evidence("RE_SCAN", "PASSED", "scan:2"),
        Evidence("RE_TRACE", "PASSED", "trace:2"),
        Evidence("CLOSURE_EVIDENCE", "PASSED", "bundle:1"),
    ]
    closed = transition_finding(finding, "CLOSED", evidence)

    assert closed["state"] == "CLOSED"
    assert closed["closure"]["status"] == "CLOSED"
    assert len(closed["closure"]["evidence"]) == 5


def test_failed_or_reference_free_evidence_does_not_count():
    finding = _finding("FIX_APPLIED_UNVERIFIED")
    evidence = [
        Evidence("FUNCTIONAL_TEST", "FAILED", "test:1"),
        Evidence("REPLAY", "PASSED", ""),
        Evidence("RE_SCAN", "PASSED", "scan:2"),
        Evidence("RE_TRACE", "PASSED", "trace:2"),
        Evidence("CLOSURE_EVIDENCE", "PASSED", "bundle:1"),
    ]

    with pytest.raises(InvalidFindingTransition):
        transition_finding(finding, "CLOSED", evidence)


def test_closed_and_disproven_are_terminal_states():
    for state in ("CLOSED", "DISPROVEN"):
        with pytest.raises(InvalidFindingTransition):
            transition_finding(_finding(state), "CANDIDATE", [])
