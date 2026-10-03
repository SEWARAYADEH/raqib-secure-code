"""Evidence-limited IDOR assessment for object lookup paths."""

from __future__ import annotations

import re


IDOR_GUARD_MISSING_CANDIDATE = "OBJECT_ACCESS_WITHOUT_OBSERVED_AUTHORIZATION_CONTROL"
IDOR_CONTROL_OBSERVED = "AUTHORIZATION_CONTROL_OBSERVED_UNVERIFIED"


def assess_idor_path(path: dict, parsed: dict) -> dict:
    controls = {item.get("category") for item in path.get("controls_observed", [])}
    observed = controls & {"authorization_check", "ownership_check"}
    if observed:
        return _result(IDOR_CONTROL_OBSERVED, "AUTHORIZATION_OR_OWNERSHIP_CONTROL_OBSERVED")
    if _terminating_ownership_guard_after_lookup(path, parsed):
        return _result(IDOR_CONTROL_OBSERVED, "TERMINATING_OWNERSHIP_GUARD_OBSERVED_AFTER_LOOKUP")
    return _result(IDOR_GUARD_MISSING_CANDIDATE, "USER_RESOURCE_ID_REACHES_OBJECT_LOOKUP")


def _result(status: str, basis: str) -> dict:
    return {
        "pack": "BROKEN_AUTHORIZATION_IDOR", "status": status, "basis": basis,
        "scope": "OBSERVED_RESOURCE_IDENTIFIER_TO_OBJECT_ACCESS",
        "actor_identity": "UNRESOLVED", "resource_owner": "UNRESOLVED",
        "runtime_effectiveness_verified": False,
    }


def _terminating_ownership_guard_after_lookup(path: dict, parsed: dict) -> bool:
    sink_line = path.get("sink", {}).get("start_line", 0)
    scope = path.get("scope", {})
    for region in parsed.get("control_regions", []):
        condition = region.get("condition", "")
        if region.get("start_line", 0) <= sink_line:
            continue
        if not (
            "!=" in condition
            and re.search(r"\b(?:owner_id|user_id)\b|\.owner_id\b", condition)
            and re.search(r"\b(?:current_user|user)\b|\.id\b", condition)
        ):
            continue
        if not (
            scope.get("start_line", 0) <= region.get("start_line", 0)
            <= scope.get("end_line", 0)
        ):
            continue
        if any(
            region.get("start_line", 0) <= call.get("start_line", 0)
            <= region.get("end_line", 0)
            and call.get("target") in {"abort", "raise_for_status"}
            for call in parsed.get("calls", [])
        ):
            return True
    return False
