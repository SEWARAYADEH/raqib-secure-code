from __future__ import annotations

from dataclasses import dataclass

from app.closure_evaluator import evaluate_closure


STATE_CANDIDATE = "CANDIDATE"
STATE_VERIFIED = "VERIFIED"
STATE_DISPROVEN = "DISPROVEN"
STATE_FIX_PROPOSED = "FIX_PROPOSED"
STATE_FIX_APPLIED_UNVERIFIED = "FIX_APPLIED_UNVERIFIED"
STATE_CLOSED = "CLOSED"

ALLOWED_TRANSITIONS = {
    STATE_CANDIDATE: {STATE_VERIFIED, STATE_DISPROVEN},
    STATE_VERIFIED: {STATE_FIX_PROPOSED},
    STATE_FIX_PROPOSED: {STATE_FIX_APPLIED_UNVERIFIED},
    STATE_FIX_APPLIED_UNVERIFIED: {STATE_CLOSED},
    STATE_DISPROVEN: set(),
    STATE_CLOSED: set(),
}

REQUIRED_CLOSURE_EVIDENCE = frozenset(
    {
        "FUNCTIONAL_TEST",
        "RUNTIME_VERIFICATION_BEFORE",
        "REPLAY",
        "RE_SCAN",
        "RE_TRACE",
        "CLOSURE_EVIDENCE",
    }
)


@dataclass(frozen=True)
class Evidence:
    kind: str
    status: str
    reference: str


class InvalidFindingTransition(ValueError):
    pass


def build_finding_lifecycle(*, finding: dict, analysis: dict,
                            saved_repair: dict | None,
                            saved_verification: dict | None = None,
                            closure_record: dict | None = None,
                            runtime_capability: dict | None = None) -> dict:
    """Report only persisted evidence; runtime gates need an isolated executor."""
    proposal = saved_repair["evidence"] if saved_repair else None
    artifact = saved_repair["patched_artifact"] if saved_repair else {"available": False}
    verification = saved_verification["evidence"] if saved_verification else None
    functional = (verification or {}).get("functional_test", {"status": "NOT_AVAILABLE"})
    runtime_before = (verification or {}).get("runtime_before", {"status": "NOT_AVAILABLE"})
    replay_after = (verification or {}).get("replay_after", {"status": "NOT_AVAILABLE"})
    static_scan = proposal.get("static_reanalysis", {}) if proposal else {}
    static_trace = proposal.get("static_retrace", {}) if proposal else {}
    static_recheck = (static_scan.get("status") == "NO_MATCH_OBSERVED"
                      and static_trace.get("status") == "OBSERVED_NON_CANDIDATE"
                      and bool(static_trace.get("after_paths")))
    if proposal:
        closure = evaluate_closure(
            finding=finding, proposal=proposal,
            functional=functional,
            runtime_before=runtime_before,
            replay_after=replay_after,
        )
        if not artifact.get("available"):
            for gate in closure["gates"]:
                if gate["name"] == "PATCH_CREATED":
                    gate["status"] = "NOT_AVAILABLE"
            closure["status"] = "CLOSURE_INCOMPLETE"
            closure["verified_closed"] = False
    else:
        closure = {"status": "CLOSURE_INCOMPLETE", "verified_closed": False,
                   "gates": []}
    stages = [
        {"id": "UNDERSTAND", "status": "OBSERVED" if finding.get("scope", {}).get("function") else "UNRESOLVED"},
        {"id": "TRACE", "status": "OBSERVED" if finding.get("trace") else "UNRESOLVED"},
        {"id": "VERIFY", "status": runtime_before["status"]},
        {"id": "ROOT_CAUSE", "status": (proposal or {}).get("root_cause", {}).get("status")
         or finding.get("root_cause", {}).get("status", "UNRESOLVED")},
        {"id": "PATCH", "status": "PROPOSED_UNVERIFIED" if artifact.get("available") else "NOT_AVAILABLE"},
        {"id": "FUNCTIONAL_TEST", "status": functional["status"]},
        {"id": "REPLAY", "status": replay_after["status"]},
        {"id": "RE_SCAN_RE_TRACE", "status": "PASS" if static_recheck else "NOT_AVAILABLE"},
        {"id": "CLOSURE", "status": closure["status"]},
    ]
    return {
        "finding_id": finding["id"],
        "finding_status": finding.get("state", "CANDIDATE"),
        "analysis_sha256": analysis.get("artifact", {}).get("sha256"),
        "stages": stages,
        "trace": finding.get("trace", []),
        "root_cause": (proposal or {}).get("root_cause") or finding.get("root_cause"),
        "patch": {"status": stages[4]["status"],
                  "original_sha256": proposal.get("original_sha256") if proposal else None,
                  "sha256": artifact.get("sha256"),
                  "download_available": bool(artifact.get("available")),
                  "diff": proposal.get("diff") if proposal else None},
        "functional_test": functional,
        "runtime_before": runtime_before,
        "replay_after": replay_after,
        "runtime_capability": runtime_capability or {
            "available": False, "status": "NOT_AVAILABLE",
            "reason": "RUNTIME_CAPABILITY_NOT_EVALUATED",
        },
        "re_scan": static_scan,
        "re_trace": static_trace,
        "closure": closure,
        "verification_evidence": {
            "available": saved_verification is not None,
            "evidence_id": saved_verification.get("evidence_id") if saved_verification else None,
            "created_at": saved_verification.get("created_at") if saved_verification else None,
        },
        "closure_record": {
            "available": closure_record is not None,
            "record_id": closure_record.get("record_id") if closure_record else None,
            "created_at": closure_record.get("created_at") if closure_record else None,
            "training_eligible": (
                closure_record.get("record", {}).get("training_eligible", False)
                if closure_record else False
            ),
        },
    }


def transition_finding(
    finding: dict,
    target_state: str,
    evidence: list[Evidence] | None = None,
) -> dict:
    current_state = finding.get("state")
    if target_state not in ALLOWED_TRANSITIONS.get(current_state, set()):
        raise InvalidFindingTransition(
            f"Finding cannot transition from {current_state} to {target_state}."
        )

    supplied = evidence or []
    if target_state == STATE_VERIFIED:
        _require_successful(supplied, {"EXPLOITABILITY_PROOF"})
    elif target_state == STATE_FIX_PROPOSED:
        _require_successful(supplied, {"ROOT_CAUSE_EVIDENCE"})
    elif target_state == STATE_FIX_APPLIED_UNVERIFIED:
        _require_successful(supplied, {"PATCH_APPLIED"})
    elif target_state == STATE_CLOSED:
        _require_successful(supplied, REQUIRED_CLOSURE_EVIDENCE)

    updated = dict(finding)
    updated["state"] = target_state
    updated["lifecycle_evidence"] = [
        {
            "kind": item.kind,
            "status": item.status,
            "reference": item.reference,
        }
        for item in supplied
    ]
    if target_state == STATE_CLOSED:
        updated["closure"] = {
            "status": STATE_CLOSED,
            "evidence": updated["lifecycle_evidence"],
        }
    return updated


def _require_successful(
    evidence: list[Evidence],
    required: set[str] | frozenset[str],
) -> None:
    passed = {
        item.kind
        for item in evidence
        if item.status == "PASSED" and item.reference.strip()
    }
    missing = sorted(required - passed)
    if missing:
        raise InvalidFindingTransition(
            "Required successful evidence is missing: " + ", ".join(missing)
        )
