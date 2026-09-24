from __future__ import annotations


REPLAY_STRATEGIES = {
    "os_command_execution": "INERT_SANDBOX_MARKER",
    "process_execution": "INERT_SANDBOX_MARKER",
    "dynamic_code_execution": "INERT_SANDBOX_MARKER",
    "sql_execution_candidate": "EPHEMERAL_DATABASE_ROLLBACK",
}


def build_verification_plans(
    finding_candidates: dict,
    *,
    isolation_runtime_available: bool,
) -> dict:
    plans = [
        _plan(candidate, isolation_runtime_available)
        for candidate in finding_candidates.get("candidates", [])
    ]
    return {
        "plans": plans,
        "counts": {
            "total": len(plans),
            "ready": sum(item["status"] == "READY" for item in plans),
            "blocked": sum(item["status"] == "BLOCKED" for item in plans),
            "executed": 0,
        },
        "claims": {
            "uploaded_code_executed": False,
            "exploitability_verified": False,
        },
    }


def _plan(candidate: dict, runtime_available: bool) -> dict:
    category = candidate["sink"]["category"]
    strategy = REPLAY_STRATEGIES.get(category, "MANUAL_POLICY_REVIEW")
    supported = strategy != "MANUAL_POLICY_REVIEW"
    ready = runtime_available and supported
    blockers = []
    if not runtime_available:
        blockers.append("ISOLATION_RUNTIME_UNAVAILABLE")
    if not supported:
        blockers.append("NO_APPROVED_NON_DESTRUCTIVE_REPLAY_STRATEGY")
    return {
        "finding_id": candidate["id"],
        "status": "READY" if ready else "BLOCKED",
        "execution_status": "NOT_RUN",
        "strategy": strategy,
        "blockers": blockers,
        "input_vector": candidate["source"]["category"],
        "target_operation": category,
        "capability_policy": {
            "network": "DENY",
            "host_filesystem": "DENY",
            "host_processes": "DENY",
            "secrets": "DENY",
            "identity": "NON_ROOT",
            "root_filesystem": "READ_ONLY",
            "scratch_space": "EPHEMERAL_QUOTA",
            "resource_limits": {
                "wall_time_seconds": 10,
                "cpu_seconds": 5,
                "memory_megabytes": 256,
                "processes": 16,
            },
        },
        "success_criteria": {
            "original_path_reproduced": "REQUIRED",
            "non_destructive_proof": "REQUIRED",
            "runtime_evidence": "REQUIRED",
        },
    }
