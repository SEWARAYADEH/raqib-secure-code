"""Derive closure solely from evidence produced by the server pipeline."""

from __future__ import annotations


REQUIRED_GATES = (
    "STATIC_FINDING_EXISTED",
    "ROOT_CAUSE_IDENTIFIED",
    "PATCH_CREATED",
    "PATCH_SYNTAX_VALID",
    "FUNCTIONAL_TEST",
    "RUNTIME_VERIFICATION_BEFORE",
    "REPLAY_AFTER_PATCH",
    "RE_SCAN",
    "RE_TRACE",
)


def evaluate_closure(
    *, finding: dict, proposal: dict, functional: dict,
    runtime_before: dict | None = None, replay_after: dict | None = None,
) -> dict:
    """Never infer runtime proof from a static recheck or a fixture test."""
    root = proposal.get("root_cause", {})
    trace = proposal.get("static_retrace", {})
    scan = proposal.get("static_reanalysis", {})
    original_sha = proposal.get("original_sha256")
    patched_sha = proposal.get("updated_sha256")
    checks = {
        "STATIC_FINDING_EXISTED": (
            "PASS" if finding.get("id") == proposal.get("finding_id")
            and finding.get("state") == "CANDIDATE" else "FAIL"
        ),
        "ROOT_CAUSE_IDENTIFIED": (
            "PASS" if root.get("status") == "STATICALLY_SUPPORTED"
            and root.get("evidence") else "NOT_AVAILABLE"
        ),
        "PATCH_CREATED": (
            "PASS" if original_sha and patched_sha and original_sha != patched_sha
            and proposal.get("diff") else "FAIL"
        ),
        "PATCH_SYNTAX_VALID": (
            "PASS" if scan.get("syntax_valid") is True else "FAIL"
        ),
        "FUNCTIONAL_TEST": _evidence_gate(functional),
        "RUNTIME_VERIFICATION_BEFORE": _evidence_gate(runtime_before),
        "REPLAY_AFTER_PATCH": _evidence_gate(replay_after),
        "RE_SCAN": (
            "PASS" if scan.get("status") == "NO_MATCH_OBSERVED" else "FAIL"
        ),
        "RE_TRACE": (
            "PASS" if trace.get("status") == "OBSERVED_NON_CANDIDATE"
            and trace.get("after_paths") else "NOT_AVAILABLE"
        ),
    }
    gates = [{"name": name, "status": checks[name]} for name in REQUIRED_GATES]
    if any(gate["status"] == "FAIL" for gate in gates):
        state = "NOT_CLOSED"
    elif all(gate["status"] == "PASS" for gate in gates):
        state = "VERIFIED_CLOSED"
    else:
        state = "CLOSURE_INCOMPLETE"
    return {"status": state, "gates": gates, "verified_closed": state == "VERIFIED_CLOSED"}


def _evidence_gate(evidence: dict | None) -> str:
    status = (evidence or {}).get("status", "NOT_AVAILABLE")
    if status in {"PASS", "NOT_AVAILABLE"}:
        return status
    return "FAIL"
