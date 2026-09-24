from __future__ import annotations

import re

from app.control_flow import (
    branch_constraints,
    build_control_flow_model,
    constraints_compatible,
    merge_constraints,
)
from app.security_semantics import (
    SEMANTIC_CONTROL,
    SEMANTIC_SINK,
    SEMANTIC_SOURCE,
)


FLOW_KIND = "SOURCE_TO_SENSITIVE_SINK_PATH"
FLOW_STATUS = "OBSERVED"


def build_intra_function_data_flow(
    parsed: dict,
    semantics: dict,
    control_flow: dict | None = None,
) -> dict:
    """Build conservative source-to-sink paths inside one function.

    This stage records evidence paths. It deliberately does not declare
    vulnerabilities, exploitability, severity, or CWE classifications.
    """

    control_flow = control_flow or build_control_flow_model(parsed)
    functions = parsed.get("functions", [])
    assignments = sorted(
        parsed.get("assignments", []),
        key=_start_position,
    )
    calls = parsed.get("calls", [])
    sources = semantics.get("sources", [])
    sinks = semantics.get("sinks", [])
    controls = semantics.get("security_controls", [])
    paths = []

    for source in sources:
        scope = _find_innermost_scope(source, functions)

        if scope is None:
            continue

        scoped_assignments = [
            item
            for item in assignments
            if _same_scope(item, scope, functions)
        ]
        scoped_sinks = [
            item
            for item in sinks
            if _same_scope(item, scope, functions)
            and (
                _start_position(item) >= _start_position(source)
                or _contains(item, source)
            )
        ]

        tainted = _seed_tainted_variables(
            source,
            scoped_assignments,
            control_flow,
            controls,
        )
        _propagate_tainted_variables(
            tainted,
            scoped_assignments,
            source,
            control_flow,
            controls,
        )

        for sink in scoped_sinks:
            sink_call = _find_matching_call(sink, calls)

            if sink_call is None:
                continue

            path = _build_path(
                source=source,
                sink=sink,
                sink_call=sink_call,
                scope=scope,
                tainted=tainted,
                control_flow=control_flow,
            )

            if path is not None:
                paths.append(path)

    return {
        "language": parsed.get("language"),
        "scope": "INTRA_FUNCTION",
        "paths": paths,
        "counts": {
            "observed_paths": len(paths),
        },
        "limitations": [
            "Only direct assignments and identifier propagation are modeled.",
            "Paths do not cross function or module boundaries.",
            "Observed paths are evidence, not vulnerability findings.",
        ],
    }


def _seed_tainted_variables(
    source: dict,
    assignments: list,
    control_flow: dict,
    controls: list,
) -> dict[str, list[dict]]:
    tainted = {}
    source_constraints = branch_constraints(
        source,
        control_flow,
    )

    for assignment in assignments:
        value_location = assignment.get(
            "value_location",
            assignment,
        )

        if not _contains(value_location, source):
            continue

        target = assignment.get("target", "")

        if not _is_identifier(target):
            continue

        assignment_constraints = branch_constraints(
            assignment,
            control_flow,
        )

        if not constraints_compatible(
            source_constraints,
            assignment_constraints,
        ):
            continue

        trace = [_source_step(source)]
        trace.extend(
            _control_steps_for_location(
                controls,
                value_location,
            )
        )
        trace.append(_assignment_step(assignment))
        tainted.setdefault(target, []).append(
            {
                "trace": trace,
                "constraints": merge_constraints(
                    source_constraints,
                    assignment_constraints,
                ),
            }
        )

    return tainted


def _propagate_tainted_variables(
    tainted: dict[str, list[dict]],
    assignments: list,
    source: dict,
    control_flow: dict,
    controls: list,
) -> None:
    for assignment in assignments:
        if _start_position(assignment) < _start_position(source):
            continue

        target = assignment.get("target", "")
        value = assignment.get("value", "")

        if not _is_identifier(target):
            continue

        assignment_constraints = branch_constraints(
            assignment,
            control_flow,
        )
        candidates = [
            state
            for name, states in list(tainted.items())
            if _mentions_identifier(value, name)
            for state in states
            if constraints_compatible(
                state["constraints"],
                assignment_constraints,
            )
        ]

        for state in candidates:
            trace = list(state["trace"])
            trace.extend(
                _control_steps_for_location(
                    controls,
                    assignment.get(
                        "value_location",
                        assignment,
                    ),
                )
            )
            trace.append(_assignment_step(assignment))
            new_state = {
                "trace": trace,
                "constraints": merge_constraints(
                    state["constraints"],
                    assignment_constraints,
                ),
            }
            states = tainted.setdefault(target, [])

            if new_state not in states:
                states.append(new_state)


def _build_path(
    *,
    source: dict,
    sink: dict,
    sink_call: dict,
    scope: dict,
    tainted: dict[str, list[dict]],
    control_flow: dict,
) -> dict | None:
    direct_source = _contains(sink_call, source)
    matched_variable = None
    matched_state = None
    sink_constraints = branch_constraints(
        sink,
        control_flow,
    )

    if not direct_source:
        argument_texts = [
            item.get("text", "")
            for item in sink_call.get(
                "argument_values",
                [],
            )
        ]
        for name, states in tainted.items():
            if not any(
                _mentions_identifier(text, name)
                for text in argument_texts
            ):
                continue

            matched_state = next(
                (
                    state
                    for state in states
                    if constraints_compatible(
                        state["constraints"],
                        sink_constraints,
                    )
                ),
                None,
            )

            if matched_state is not None:
                matched_variable = name
                break

        if matched_state is None:
            return None

    elif not constraints_compatible(
        branch_constraints(source, control_flow),
        sink_constraints,
    ):
        return None

    trace = (
        [_source_step(source)]
        if direct_source
        else list(matched_state["trace"])
    )
    trace.append(_sink_step(sink, matched_variable))
    path_constraints = (
        merge_constraints(
            branch_constraints(source, control_flow),
            sink_constraints,
        )
        if direct_source
        else merge_constraints(
            matched_state["constraints"],
            sink_constraints,
        )
    )
    controls_observed = [
        step
        for step in trace
        if step["kind"] == SEMANTIC_CONTROL
    ]

    evidence_strength = (
        "DIRECT"
        if source.get("evidence_strength") == "DIRECT"
        and sink.get("evidence_strength") == "DIRECT"
        else "HEURISTIC"
    )

    return {
        "kind": FLOW_KIND,
        "status": FLOW_STATUS,
        "scope": {
            "function": scope.get("name"),
            "start_line": scope.get("start_line"),
            "end_line": scope.get("end_line"),
        },
        "source": _semantic_endpoint(source),
        "sink": _semantic_endpoint(sink),
        "trace": trace,
        "branch_constraints": path_constraints,
        "controls_observed": controls_observed,
        "control_assessment": (
            "UNVERIFIED_APPLICABILITY"
            if controls_observed
            else "NONE_OBSERVED"
        ),
        "evidence_strength": evidence_strength,
    }


def _find_matching_call(
    observation: dict,
    calls: list,
) -> dict | None:
    return next(
        (
            call
            for call in calls
            if call.get("target") == observation.get("target")
            and _same_location(call, observation)
        ),
        None,
    )


def _find_innermost_scope(
    item: dict,
    functions: list,
) -> dict | None:
    candidates = [
        function
        for function in functions
        if _contains(function, item)
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda function: (
            function["end_line"]
            - function["start_line"],
            function["end_column"]
            - function["start_column"],
        ),
    )


def _same_scope(
    item: dict,
    scope: dict,
    functions: list,
) -> bool:
    return _find_innermost_scope(item, functions) is scope


def _contains(outer: dict, inner: dict) -> bool:
    return (
        _start_position(outer) <= _start_position(inner)
        and _end_position(outer) >= _end_position(inner)
    )


def _same_location(left: dict, right: dict) -> bool:
    return (
        _start_position(left) == _start_position(right)
        and _end_position(left) == _end_position(right)
    )


def _start_position(item: dict) -> tuple[int, int]:
    return (
        item.get("start_line", 0),
        item.get("start_column", 0),
    )


def _end_position(item: dict) -> tuple[int, int]:
    return (
        item.get("end_line", 0),
        item.get("end_column", 0),
    )


def _is_identifier(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[A-Za-z_$][A-Za-z0-9_$]*",
            value,
        )
    )


def _mentions_identifier(text: str, identifier: str) -> bool:
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9_$]){re.escape(identifier)}"
            rf"(?![A-Za-z0-9_$])",
            text,
        )
    )


def _semantic_endpoint(item: dict) -> dict:
    return {
        "rule_id": item["rule_id"],
        "kind": item["kind"],
        "category": item["category"],
        "target": item["target"],
        "start_line": item["start_line"],
        "end_line": item["end_line"],
        "start_column": item["start_column"],
        "end_column": item["end_column"],
    }


def _control_steps_for_location(
    controls: list,
    location: dict,
) -> list[dict]:
    return [
        {
            "kind": SEMANTIC_CONTROL,
            "rule_id": control["rule_id"],
            "category": control["category"],
            "target": control["target"],
            "line": control["start_line"],
            "assessment": "UNVERIFIED_APPLICABILITY",
        }
        for control in controls
        if _contains(location, control)
    ]


def _source_step(source: dict) -> dict:
    assert source["kind"] == SEMANTIC_SOURCE

    return {
        "kind": SEMANTIC_SOURCE,
        "target": source["target"],
        "line": source["start_line"],
    }


def _assignment_step(assignment: dict) -> dict:
    return {
        "kind": "ASSIGNMENT",
        "target": assignment["target"],
        "value": assignment["value"],
        "line": assignment["start_line"],
    }


def _sink_step(
    sink: dict,
    variable: str | None,
) -> dict:
    assert sink["kind"] == SEMANTIC_SINK

    return {
        "kind": SEMANTIC_SINK,
        "target": sink["target"],
        "via": variable,
        "line": sink["start_line"],
    }
