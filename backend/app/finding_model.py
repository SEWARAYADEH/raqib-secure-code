from __future__ import annotations

import hashlib
import json


STANDARD_CANDIDATES = {
    "os_command_execution": {
        "cwe": "CWE-78",
        "owasp": "A03:2021-Injection",
    },
    "process_execution": {
        "cwe": "CWE-78",
        "owasp": "A03:2021-Injection",
    },
    "dynamic_code_execution": {
        "cwe": "CWE-95",
        "owasp": "A03:2021-Injection",
    },
    "sql_execution_candidate": {
        "cwe": "CWE-89",
        "owasp": "A03:2021-Injection",
    },
}


def build_finding_candidates(
    *,
    artifact: dict,
    intra_function_flow: dict,
    inter_function_flow: dict,
) -> dict:
    paths = [
        *(intra_function_flow.get("paths", [])),
        *(inter_function_flow.get("paths", [])),
    ]
    candidates = [
        _candidate_from_path(artifact, path)
        for path in paths
    ]
    return {
        "schema_version": "1.0",
        "candidates": candidates,
        "counts": {
            "candidates": len(candidates),
            "verified_vulnerabilities": 0,
            "closed_findings": 0,
        },
        "policy": {
            "observed_path_is_vulnerability": False,
            "ai_can_verify_or_close": False,
            "closure_requires": [
                "FUNCTIONAL_TEST",
                "REPLAY",
                "RE_SCAN",
                "RE_TRACE",
                "CLOSURE_EVIDENCE",
            ],
        },
    }


def _candidate_from_path(artifact: dict, path: dict) -> dict:
    sink_category = path["sink"]["category"]
    standard = STANDARD_CANDIDATES.get(sink_category)
    controls = path.get("controls_observed", [])
    identity = {
        "artifact_sha256": artifact["sha256"],
        "kind": path["kind"],
        "source": path["source"],
        "sink": path["sink"],
        "scope": path["scope"],
    }
    return {
        "id": _stable_id(identity),
        "state": "CANDIDATE",
        "classification": "SECURITY_FINDING_CANDIDATE",
        "title": f"Observed input flow to {sink_category}",
        "evidence_strength": path["evidence_strength"],
        "reachability": {
            "static_path": "OBSERVED",
            "runtime_reachability": "UNVERIFIED",
            "input_influence": "OBSERVED_STATIC_FLOW",
            "preconditions": "UNRESOLVED",
        },
        "exploitability": {
            "status": "UNVERIFIED",
            "proof": None,
            "safe_replay_required": True,
        },
        "root_cause": {
            "status": "CANDIDATE",
            "statement": (
                "Untrusted input reaches a sensitive operation without a "
                "verified effective control on the observed static path."
            ),
        },
        "source": path["source"],
        "sink": path["sink"],
        "scope": path["scope"],
        "trace": path["trace"],
        "controls": {
            "observed": controls,
            "assessment": path.get(
                "control_assessment",
                "NONE_OBSERVED",
            ),
            "effectiveness": "UNVERIFIED" if controls else "NOT_OBSERVED",
        },
        "standards": (
            {
                **standard,
                "status": "CANDIDATE_MAPPING",
                "basis": sink_category,
            }
            if standard
            else {
                "cwe": "UNRESOLVED",
                "owasp": "UNRESOLVED",
                "status": "UNRESOLVED",
                "basis": sink_category,
            }
        ),
        "remediation": {
            "status": "NOT_PROPOSED",
            "minimal_patch": None,
        },
        "closure": {
            "status": "NOT_ELIGIBLE",
            "evidence": [],
        },
    }


def _stable_id(identity: dict) -> str:
    encoded = json.dumps(
        identity,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "finding:" + hashlib.sha256(encoded).hexdigest()[:24]
