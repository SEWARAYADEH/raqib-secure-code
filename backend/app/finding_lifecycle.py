from __future__ import annotations

from dataclasses import dataclass


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
