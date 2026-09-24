from __future__ import annotations

from app.interprocedural_flow import (
    build_parameter_sink_evidence,
    build_source_argument_evidence,
)
from app.security_semantics import SEMANTIC_CONTROL


FLOW_KIND = "PROJECT_SOURCE_TO_SENSITIVE_SINK_PATH"
FLOW_STATUS = "OBSERVED"
FLOW_SCOPE = "CROSS_FILE_ONE_BOUNDARY"


def build_project_data_flow(
    file_results: list[dict],
    cross_file_calls: list[dict],
) -> dict:
    """Build conservative source-to-sink evidence across one proven file boundary.

    Only statically resolved cross-file calls supplied by project call resolution
    are followed. This function records evidence paths; it does not declare a
    vulnerability, exploitability, severity, or closure.
    """
    files = {
        item["artifact"]["relative_path"]: item
        for item in file_results
    }
    paths = []

    for relationship in cross_file_calls:
        source = files.get(relationship["source_file"])
        target = files.get(relationship["target_file"])
        if source is None or target is None:
            continue

        if (
            source["language"]["candidate"] != "Python"
            or target["language"]["candidate"] != "Python"
        ):
            continue

        source_evidence = build_source_argument_evidence(
            parsed=source["structure"],
            relationships=source["relationships"],
            semantics=source["security_semantics"],
            control_flow=source["control_flow"],
            caller_id=relationship["caller_id"],
            call_target=_source_call_target(
                source,
                relationship,
            ),
            call_line=relationship["call_line"],
        )
        if not source_evidence:
            continue

        sink_evidence = build_parameter_sink_evidence(
            parsed=target["structure"],
            relationships=target["relationships"],
            semantics=target["security_semantics"],
            control_flow=target["control_flow"],
            callee_id=relationship["callee_id"],
        )
        if not sink_evidence:
            continue

        for source_item in source_evidence:
            for sink_item in sink_evidence:
                if (
                    source_item["argument_index"]
                    != sink_item["parameter_index"]
                ):
                    continue

                trace = [
                    *[
                        {
                            **step,
                            "file": relationship["source_file"],
                        }
                        for step in source_item["trace"]
                    ],
                    {
                        "kind": "PROJECT_CALL_BOUNDARY",
                        "source_file": relationship["source_file"],
                        "target_file": relationship["target_file"],
                        "caller": relationship["caller"],
                        "callee": relationship["callee"],
                        "line": relationship["call_line"],
                        "resolution": relationship["resolution"],
                        "argument_index": source_item[
                            "argument_index"
                        ],
                        "parameter_name": sink_item[
                            "parameter_name"
                        ],
                    },
                    *[
                        {
                            **step,
                            "file": relationship["target_file"],
                        }
                        for step in sink_item["trace"]
                    ],
                ]
                controls = [
                    step
                    for step in trace
                    if step.get("kind") == SEMANTIC_CONTROL
                ]
                paths.append(
                    {
                        "kind": FLOW_KIND,
                        "status": FLOW_STATUS,
                        "scope": FLOW_SCOPE,
                        "source_file": relationship["source_file"],
                        "target_file": relationship["target_file"],
                        "caller": relationship["caller"],
                        "callee": relationship["callee"],
                        "call_line": relationship["call_line"],
                        "source": source_item["source"],
                        "sink": sink_item["sink"],
                        "trace": trace,
                        "controls_observed": controls,
                        "control_assessment": (
                            "UNVERIFIED_APPLICABILITY"
                            if controls
                            else "NONE_OBSERVED"
                        ),
                        "evidence_strength": _combined_strength(
                            source_item["evidence_strength"],
                            sink_item["evidence_strength"],
                        ),
                    }
                )

    paths.sort(
        key=lambda item: (
            item["source_file"],
            item["call_line"],
            item["target_file"],
            item["sink"]["start_line"],
        )
    )
    return {
        "scope": FLOW_SCOPE,
        "paths": paths,
        "counts": {
            "observed_paths": len(paths),
        },
        "limitations": [
            "Only statically resolved Python cross-file calls are followed.",
            "The current project trace crosses exactly one file boundary.",
            "Argument-to-parameter binding is positional only.",
            "Observed paths are evidence, not vulnerability findings.",
            "Exploitability is not established by this stage.",
        ],
    }


def _source_call_target(
    source_result: dict,
    relationship: dict,
) -> str:
    candidates = [
        item["call_target"]
        for item in source_result["relationships"][
            "unresolved_calls"
        ]
        if item["caller_id"] == relationship["caller_id"]
        and item["line"] == relationship["call_line"]
    ]
    return candidates[0] if len(candidates) == 1 else ""


def _combined_strength(
    source_strength: str,
    sink_strength: str,
) -> str:
    return (
        "DIRECT"
        if source_strength == "DIRECT"
        and sink_strength == "DIRECT"
        else "HEURISTIC"
    )
