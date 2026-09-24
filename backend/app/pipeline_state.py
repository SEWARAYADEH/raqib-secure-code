from __future__ import annotations


def build_pipeline_state(
    *,
    findings: dict,
    verification: dict,
) -> dict:
    has_candidates = findings["counts"]["candidates"] > 0
    verification_blocked = verification["counts"]["blocked"] > 0
    stages = [
        _stage("SAFE_INTAKE", "COMPLETED"),
        _stage("LANGUAGE_INTELLIGENCE", "COMPLETED"),
        _stage("PARSING", "COMPLETED"),
        _stage("APPLICATION_UNDERSTANDING", "COMPLETED"),
        _stage("APPLICATION_GRAPH", "COMPLETED"),
        _stage("SECURITY_SEMANTICS", "COMPLETED"),
        _stage("DATA_FLOW_TRACE", "COMPLETED"),
        _stage(
            "SECURITY_ANALYSIS",
            "CANDIDATES_OBSERVED" if has_candidates else "COMPLETED_NO_CANDIDATE",
        ),
        _stage(
            "EXPLOITABILITY_VERIFICATION",
            "BLOCKED" if verification_blocked else "NOT_RUN",
            (
                ["ISOLATION_RUNTIME_UNAVAILABLE"]
                if verification_blocked
                else []
            ),
        ),
        _stage("ROOT_CAUSE", "CANDIDATE_ONLY" if has_candidates else "NOT_REQUIRED"),
        _stage("MINIMAL_SECURE_PATCH", "BLOCKED" if has_candidates else "NOT_REQUIRED", ["EXPLOITABILITY_NOT_VERIFIED"] if has_candidates else []),
        _stage("FUNCTIONAL_VERIFICATION", "NOT_RUN"),
        _stage("RE_SCAN", "NOT_RUN"),
        _stage("RE_TRACE", "NOT_RUN"),
        _stage("REPLAY", "NOT_RUN"),
        _stage("EVIDENCE_OF_CLOSURE", "NOT_AVAILABLE"),
        _stage("REPORT", "PARTIAL_EVIDENCE_REPORT"),
        _stage("DOWNLOAD_UPDATED_ARTIFACT", "NOT_AVAILABLE", ["NO_VERIFIED_PATCH"]),
    ]
    return {
        "stages": stages,
        "current_stage": (
            "EXPLOITABILITY_VERIFICATION"
            if has_candidates
            else "SECURITY_ANALYSIS"
        ),
        "updated_artifact": {
            "status": "NOT_AVAILABLE",
            "reason": "NO_VERIFIED_PATCH",
            "original_overwritten": False,
        },
        "claims": {
            "vulnerability_verified": False,
            "patch_generated": False,
            "finding_closed": False,
        },
    }


def _stage(name: str, status: str, blockers: list[str] | None = None) -> dict:
    return {
        "name": name,
        "status": status,
        "blockers": blockers or [],
    }
