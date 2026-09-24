from __future__ import annotations

from collections import Counter


def build_control_flow_model(parsed: dict) -> dict:
    regions = parsed.get("control_regions", [])
    kinds = Counter(region["kind"] for region in regions)
    groups = {
        region["group_id"]
        for region in regions
    }

    return {
        "scope": "INTRA_FUNCTION_BRANCH_REGIONS",
        "regions": regions,
        "counts": {
            "groups": len(groups),
            "regions": len(regions),
            "regions_by_kind": dict(sorted(kinds.items())),
        },
        "claims": {
            "full_control_flow_graph": False,
            "path_feasibility_proven": False,
        },
    }


def branch_constraints(
    item: dict,
    control_flow: dict,
) -> dict[str, str]:
    matching = [
        region
        for region in control_flow.get("regions", [])
        if _contains(region, item)
    ]

    return {
        region["group_id"]: region["branch_id"]
        for region in matching
    }


def constraints_compatible(
    left: dict[str, str],
    right: dict[str, str],
) -> bool:
    return all(
        group_id not in right
        or right[group_id] == branch_id
        for group_id, branch_id in left.items()
    )


def merge_constraints(
    left: dict[str, str],
    right: dict[str, str],
) -> dict[str, str]:
    if not constraints_compatible(left, right):
        raise ValueError("Mutually exclusive branch constraints.")

    return {**left, **right}


def _contains(outer: dict, inner: dict) -> bool:
    return (
        (outer["start_line"], outer["start_column"])
        <= (inner["start_line"], inner["start_column"])
        and (outer["end_line"], outer["end_column"])
        >= (inner["end_line"], inner["end_column"])
    )
