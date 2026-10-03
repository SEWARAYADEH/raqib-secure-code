from __future__ import annotations

import hashlib
import json

from app.security_packs.sql_injection import (
    QUERY_TEXT_INFLUENCE,
    assess_sql_path,
)
from app.security_packs.command_injection import (
    NON_SHELL_ARGUMENT_FLOW,
    assess_command_path,
)
from app.security_packs.path_traversal import (
    PATH_CONTROL_OBSERVED,
    PATH_INFLUENCE_CANDIDATE,
    assess_path_path,
)
from app.security_packs.xss import (
    XSS_CONTROL_OBSERVED,
    assess_xss_path,
)
from app.security_packs.broken_authorization import (
    IDOR_CONTROL_OBSERVED,
    assess_idor_path,
)


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
    "filesystem_path_operation": {
        "cwe": "CWE-22",
        "owasp": "A01:2021-Broken Access Control",
    },
    "html_dom_rendering": {
        "cwe": "CWE-79",
        "owasp": "A03:2021-Injection",
    },
    "authorization_sensitive_object_access": {
        "cwe": "CWE-639",
        "owasp": "A01:2021-Broken Access Control",
    },
}


def build_finding_candidates(
    *,
    artifact: dict,
    parsed: dict,
    intra_function_flow: dict,
    inter_function_flow: dict,
) -> dict:
    paths = [
        *(intra_function_flow.get("paths", [])),
        *(inter_function_flow.get("paths", [])),
    ]
    candidates = []
    non_candidates = []
    for path in paths:
        if path["sink"]["category"] == "sql_execution_candidate":
            assessment = assess_sql_path(path, parsed)
            if assessment["status"] != QUERY_TEXT_INFLUENCE:
                non_candidates.append({
                    "source": path["source"],
                    "sink": path["sink"],
                    "scope": path["scope"],
                    "trace": path["trace"],
                    "assessment": assessment,
                })
                continue
            candidate = _candidate_from_path(artifact, path)
            candidate["pack_assessment"] = assessment
            candidates.append(candidate)
        elif path["sink"]["category"] == "process_execution":
            assessment = assess_command_path(path, parsed)
            if assessment["status"] == NON_SHELL_ARGUMENT_FLOW:
                non_candidates.append({
                    "source": path["source"],
                    "sink": path["sink"],
                    "scope": path["scope"],
                    "trace": path["trace"],
                    "assessment": assessment,
                })
                continue
            candidate = _candidate_from_path(artifact, path)
            candidate["pack_assessment"] = assessment
            candidates.append(candidate)
        elif path["sink"]["category"] == "filesystem_path_operation":
            assessment = assess_path_path(path, parsed)
            if assessment["status"] == PATH_CONTROL_OBSERVED:
                non_candidates.append({
                    "source": path["source"],
                    "sink": path["sink"],
                    "scope": path["scope"],
                    "trace": path["trace"],
                    "assessment": assessment,
                })
                continue
            candidate = _candidate_from_path(artifact, path)
            candidate["pack_assessment"] = assessment
            candidates.append(candidate)
        elif path["sink"]["category"] == "html_dom_rendering":
            assessment = assess_xss_path(path, parsed)
            if assessment["status"] == XSS_CONTROL_OBSERVED:
                non_candidates.append({"source": path["source"], "sink": path["sink"],
                                       "scope": path["scope"],
                                       "trace": path["trace"], "assessment": assessment})
                continue
            candidate = _candidate_from_path(artifact, path)
            candidate["pack_assessment"] = assessment
            candidates.append(candidate)
        elif path["sink"]["category"] == "authorization_sensitive_object_access":
            assessment = assess_idor_path(path, parsed)
            if assessment["status"] == IDOR_CONTROL_OBSERVED:
                non_candidates.append({"source": path["source"], "sink": path["sink"],
                                       "scope": path["scope"],
                                       "trace": path["trace"], "assessment": assessment})
                continue
            candidate = _candidate_from_path(artifact, path)
            candidate["pack_assessment"] = assessment
            candidates.append(candidate)
        else:
            candidates.append(_candidate_from_path(artifact, path))
    return {
        "schema_version": "1.0",
        "candidates": candidates,
        "non_candidates": non_candidates,
        "counts": {
            "candidates": len(candidates),
            "non_candidate_paths": len(non_candidates),
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


def build_project_finding_candidates(
    *, artifact: dict, paths: list[dict], file_results: list[dict]
) -> dict:
    parsed_by_file = {
        item["artifact"]["relative_path"]: item["structure"]
        for item in file_results
    }
    candidates = []
    non_candidates = []
    for path in paths:
        parsed = parsed_by_file[path["target_file"]]
        candidate, non_candidate = _assess_candidate_path(artifact, path, parsed)
        if candidate:
            candidate["cross_file"] = {
                "source_file": path["source_file"],
                "target_file": path["target_file"],
                "resolution": path["resolution"],
            }
            candidates.append(candidate)
        elif non_candidate:
            non_candidates.append(non_candidate)
    return {
        "schema_version": "1.0",
        "scope": "PROJECT_CROSS_FILE",
        "candidates": candidates,
        "non_candidates": non_candidates,
        "counts": {
            "candidates": len(candidates),
            "non_candidate_paths": len(non_candidates),
            "verified_vulnerabilities": 0,
            "closed_findings": 0,
        },
    }


def _assess_candidate_path(
    artifact: dict, path: dict, parsed: dict
) -> tuple[dict | None, dict | None]:
    category = path["sink"]["category"]
    assessment = None
    candidate_status = True
    if category == "sql_execution_candidate":
        assessment = assess_sql_path(path, parsed)
        candidate_status = assessment["status"] == QUERY_TEXT_INFLUENCE
    elif category == "process_execution":
        assessment = assess_command_path(path, parsed)
        candidate_status = assessment["status"] != NON_SHELL_ARGUMENT_FLOW
    elif category == "filesystem_path_operation":
        assessment = assess_path_path(path, parsed)
        candidate_status = assessment["status"] != PATH_CONTROL_OBSERVED
    elif category == "html_dom_rendering":
        assessment = assess_xss_path(path, parsed)
        candidate_status = assessment["status"] != XSS_CONTROL_OBSERVED
    elif category == "authorization_sensitive_object_access":
        assessment = assess_idor_path(path, parsed)
        candidate_status = assessment["status"] != IDOR_CONTROL_OBSERVED
    if not candidate_status:
        return None, {
            "source": path["source"], "sink": path["sink"],
            "scope": path["scope"],
            "trace": path["trace"], "assessment": assessment,
        }
    candidate = _candidate_from_path(artifact, path)
    if assessment:
        candidate["pack_assessment"] = assessment
    return candidate, None


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
