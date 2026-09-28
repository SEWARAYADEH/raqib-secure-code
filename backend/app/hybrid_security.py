"""Keep rule, flow, context, and advisory evidence distinct while correlating it."""

from __future__ import annotations


def correlate_file_evidence(
    *, semantics: dict, understanding: dict, findings: dict
) -> dict:
    correlations = []
    for candidate in findings["candidates"]:
        correlations.append(
            {
                "candidate_id": candidate["id"],
                "state": "CANDIDATE",
                "source_rule_id": candidate["source"]["rule_id"],
                "sink_rule_id": candidate["sink"]["rule_id"],
                "trace_evidence": "OBSERVED_STATIC_PATH",
                "control_effectiveness": candidate["controls"]["effectiveness"],
                "standards": candidate["standards"],
                "runtime_reachability": "UNVERIFIED",
                "exploitability": "UNVERIFIED",
            }
        )
    return {
        "sensors": {
            "syntax_parser": "COMPLETED",
            "semantic_rules": "COMPLETED",
            "static_data_flow": "COMPLETED_BOUNDED",
            "application_context": "COMPLETED_STATIC",
            "external_sast": "NOT_RUN",
            "dependency_advisories": "NOT_APPLICABLE_TO_SINGLE_FILE",
        },
        "observations": {
            "sources": semantics["counts"]["sources"],
            "sinks": semantics["counts"]["sinks"],
            "controls": semantics["counts"]["security_controls"],
            "frameworks": len(understanding.get("frameworks", [])),
        },
        "correlations": correlations,
        "claims": {
            "vulnerability_verified": False,
            "external_sast_reconciled": False,
            "runtime_context_verified": False,
        },
    }


def correlate_project_evidence(
    file_results: list[dict], dependency_advisories: dict
) -> dict:
    code_correlations = [
        {"file": file_result["artifact"]["relative_path"], **item}
        for file_result in file_results
        for item in file_result["hybrid_security"]["correlations"]
    ]
    return {
        "sensors": {
            "syntax_parser": "COMPLETED_FOR_SUPPORTED_FILES",
            "semantic_rules": "COMPLETED_FOR_SUPPORTED_FILES",
            "static_data_flow": "COMPLETED_BOUNDED",
            "application_context": "COMPLETED_STATIC",
            "external_sast": "NOT_RUN",
            "dependency_advisories": dependency_advisories["status"],
        },
        "code_correlations": code_correlations,
        "dependency_advisory_matches": dependency_advisories[
            "advisory_matches"
        ],
        "counts": {
            "code_candidates": len(code_correlations),
            "dependency_advisory_matches": dependency_advisories[
                "counts"
            ]["advisory_matches"],
            "verified_vulnerabilities": 0,
        },
        "policy": {
            "code_and_dependency_results_independent": True,
            "advisory_match_proves_installed_version": False,
            "advisory_match_proves_reachability": False,
            "candidate_mapping_proves_vulnerability": False,
        },
    }
