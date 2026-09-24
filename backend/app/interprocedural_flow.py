from __future__ import annotations

import re

from app.control_flow import (
    branch_constraints,
    constraints_compatible,
    merge_constraints,
)
from app.security_semantics import SEMANTIC_CONTROL


FLOW_KIND = "INTER_FUNCTION_SOURCE_TO_SENSITIVE_SINK_PATH"


def build_inter_function_data_flow(
    *,
    parsed: dict,
    relationships: dict,
    semantics: dict,
    control_flow: dict,
) -> dict:
    symbols = relationships.get("symbols", [])
    symbols_by_id = {
        symbol["id"]: symbol for symbol in symbols
    }
    assignments = parsed.get("assignments", [])
    calls = parsed.get("calls", [])
    controls = semantics.get("security_controls", [])
    parameter_summaries = _build_parameter_sink_summaries(
        symbols=symbols,
        assignments=assignments,
        calls=calls,
        sinks=semantics.get("sinks", []),
        controls=controls,
        control_flow=control_flow,
    )
    paths = []

    for relationship in relationships.get(
        "relationships",
        [],
    ):
        caller = symbols_by_id[relationship["caller_id"]]
        callee = symbols_by_id[relationship["callee_id"]]
        call = _find_relationship_call(
            relationship,
            caller,
            calls,
        )

        if call is None:
            continue

        summaries = parameter_summaries.get(callee["id"], [])

        if not summaries:
            continue

        caller_sources = [
            source
            for source in semantics.get("sources", [])
            if _find_scope(source, symbols) is caller
        ]

        for source in caller_sources:
            source_states = _build_source_states(
                source=source,
                scope=caller,
                symbols=symbols,
                assignments=assignments,
                controls=controls,
                control_flow=control_flow,
            )

            for summary in summaries:
                argument = _argument_at(
                    call,
                    summary["parameter_index"],
                )

                if argument is None:
                    continue

                caller_trace = _trace_source_to_argument(
                    source=source,
                    source_states=source_states,
                    argument=argument,
                    call=call,
                    control_flow=control_flow,
                )

                if caller_trace is None:
                    continue

                trace = [
                    *caller_trace,
                    {
                        "kind": "CALL_BOUNDARY",
                        "caller": caller["qualified_name"],
                        "callee": callee["qualified_name"],
                        "target": call["target"],
                        "line": call["start_line"],
                    },
                    *summary["trace"],
                ]
                observed_controls = [
                    step
                    for step in trace
                    if step["kind"] == SEMANTIC_CONTROL
                ]
                paths.append(
                    {
                        "kind": FLOW_KIND,
                        "status": "OBSERVED",
                        "scope": {
                            "caller": caller[
                                "qualified_name"
                            ],
                            "callee": callee[
                                "qualified_name"
                            ],
                            "call_depth": 1,
                        },
                        "source": _endpoint(source),
                        "sink": _endpoint(summary["sink"]),
                        "trace": trace,
                        "controls_observed": observed_controls,
                        "control_assessment": (
                            "UNVERIFIED_APPLICABILITY"
                            if observed_controls
                            else "NONE_OBSERVED"
                        ),
                        "evidence_strength": (
                            "DIRECT"
                            if source["evidence_strength"]
                            == "DIRECT"
                            and summary["sink"][
                                "evidence_strength"
                            ]
                            == "DIRECT"
                            else "HEURISTIC"
                        ),
                    }
                )

    return {
        "language": parsed.get("language"),
        "scope": "INTER_FUNCTION_ONE_BOUNDARY",
        "paths": paths,
        "counts": {"observed_paths": len(paths)},
        "limitations": [
            "Only verified local call relationships are followed.",
            "The current model crosses exactly one call boundary.",
            "Observed paths are evidence, not vulnerability findings.",
        ],
    }



def build_source_argument_evidence(
    *,
    parsed: dict,
    relationships: dict,
    semantics: dict,
    control_flow: dict,
    caller_id: str,
    call_target: str,
    call_line: int,
) -> list[dict]:
    """Return proven source-to-argument evidence for one resolved call."""
    symbols = relationships.get("symbols", [])
    caller = next(
        (item for item in symbols if item["id"] == caller_id),
        None,
    )
    if caller is None:
        return []

    calls = [
        call
        for call in parsed.get("calls", [])
        if call.get("target") == call_target
        and call.get("start_line") == call_line
        and _contains(caller, call)
    ]
    if len(calls) != 1:
        return []

    call = calls[0]
    controls = semantics.get("security_controls", [])
    evidence = []
    for source in semantics.get("sources", []):
        if _find_scope(source, symbols) is not caller:
            continue

        states = _build_source_states(
            source=source,
            scope=caller,
            symbols=symbols,
            assignments=parsed.get("assignments", []),
            controls=controls,
            control_flow=control_flow,
        )
        for argument_index, argument in enumerate(
            call.get("argument_values", [])
        ):
            trace = _trace_source_to_argument(
                source=source,
                source_states=states,
                argument=argument,
                call=call,
                control_flow=control_flow,
            )
            if trace is None:
                continue
            evidence.append(
                {
                    "argument_index": argument_index,
                    "source": _endpoint(source),
                    "trace": trace,
                    "controls_observed": [
                        step
                        for step in trace
                        if step["kind"] == SEMANTIC_CONTROL
                    ],
                    "evidence_strength": source.get(
                        "evidence_strength",
                        "HEURISTIC",
                    ),
                }
            )
    return evidence


def build_parameter_sink_evidence(
    *,
    parsed: dict,
    relationships: dict,
    semantics: dict,
    control_flow: dict,
    callee_id: str,
) -> list[dict]:
    """Return proven parameter-to-sink evidence for one local function."""
    symbols = relationships.get("symbols", [])
    summaries = _build_parameter_sink_summaries(
        symbols=symbols,
        assignments=parsed.get("assignments", []),
        calls=parsed.get("calls", []),
        sinks=semantics.get("sinks", []),
        controls=semantics.get("security_controls", []),
        control_flow=control_flow,
    )
    evidence = []
    for summary in summaries.get(callee_id, []):
        trace = list(summary["trace"])
        evidence.append(
            {
                "parameter_index": summary["parameter_index"],
                "parameter_name": summary["parameter_name"],
                "sink": _endpoint(summary["sink"]),
                "trace": trace,
                "controls_observed": [
                    step
                    for step in trace
                    if step["kind"] == SEMANTIC_CONTROL
                ],
                "evidence_strength": summary["sink"].get(
                    "evidence_strength",
                    "HEURISTIC",
                ),
            }
        )
    return evidence


def _build_parameter_sink_summaries(
    *,
    symbols: list,
    assignments: list,
    calls: list,
    sinks: list,
    controls: list,
    control_flow: dict,
) -> dict[str, list[dict]]:
    summaries = {}

    for symbol in symbols:
        scoped_assignments = _items_in_scope(
            assignments,
            symbol,
            symbols,
        )
        scoped_sinks = _items_in_scope(
            sinks,
            symbol,
            symbols,
        )

        for parameter_index, parameter in enumerate(
            symbol.get("parameter_values", [])
        ):
            parameter_name = parameter.get("text", "")

            if not _is_identifier(parameter_name):
                continue

            states = {
                parameter_name: [
                    {
                        "trace": [
                            {
                                "kind": "PARAMETER",
                                "name": parameter_name,
                                "index": parameter_index,
                                "function": symbol[
                                    "qualified_name"
                                ],
                            }
                        ],
                        "constraints": {},
                        "last_position": (
                            symbol["start_line"],
                            symbol["start_column"],
                        ),
                    }
                ]
            }
            _propagate(
                states=states,
                assignments=scoped_assignments,
                controls=controls,
                control_flow=control_flow,
            )

            for sink in scoped_sinks:
                sink_call = _matching_call(sink, calls)
                match = _state_reaching_call(
                    states,
                    sink_call,
                    control_flow,
                )

                if match is None:
                    continue

                variable, state = match
                summaries.setdefault(symbol["id"], []).append(
                    {
                        "parameter_index": parameter_index,
                        "parameter_name": parameter_name,
                        "sink": sink,
                        "trace": [
                            *state["trace"],
                            {
                                "kind": "SINK",
                                "target": sink["target"],
                                "via": variable,
                                "line": sink["start_line"],
                            },
                        ],
                    }
                )

    return summaries


def _build_source_states(
    *,
    source: dict,
    scope: dict,
    symbols: list,
    assignments: list,
    controls: list,
    control_flow: dict,
) -> dict[str, list[dict]]:
    states = {}
    source_constraints = branch_constraints(
        source,
        control_flow,
    )

    for assignment in _items_in_scope(
        assignments,
        scope,
        symbols,
    ):
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

        states.setdefault(target, []).append(
            {
                "trace": [
                    {
                        "kind": "SOURCE",
                        "target": source["target"],
                        "line": source["start_line"],
                    },
                    * _control_steps(
                        controls,
                        value_location,
                    ),
                    _assignment_step(assignment),
                ],
                "constraints": merge_constraints(
                    source_constraints,
                    assignment_constraints,
                ),
                "last_position": _end_position(assignment),
            }
        )

    _propagate(
        states=states,
        assignments=_items_in_scope(
            assignments,
            scope,
            symbols,
        ),
        controls=controls,
        control_flow=control_flow,
    )
    return states


def _propagate(
    *,
    states: dict[str, list[dict]],
    assignments: list,
    controls: list,
    control_flow: dict,
) -> None:
    for assignment in sorted(assignments, key=_start_position):
        target = assignment.get("target", "")

        if not _is_identifier(target):
            continue

        value = assignment.get("value", "")
        assignment_constraints = branch_constraints(
            assignment,
            control_flow,
        )
        candidates = [
            state
            for name, name_states in list(states.items())
            if _mentions_identifier(value, name)
            for state in name_states
            if state["last_position"] <= _start_position(assignment)
            and constraints_compatible(
                state["constraints"],
                assignment_constraints,
            )
        ]

        for state in candidates:
            new_state = {
                "trace": [
                    *state["trace"],
                    *_control_steps(
                        controls,
                        assignment.get(
                            "value_location",
                            assignment,
                        ),
                    ),
                    _assignment_step(assignment),
                ],
                "constraints": merge_constraints(
                    state["constraints"],
                    assignment_constraints,
                ),
                "last_position": _end_position(assignment),
            }
            target_states = states.setdefault(target, [])

            if new_state not in target_states:
                target_states.append(new_state)


def _trace_source_to_argument(
    *,
    source: dict,
    source_states: dict[str, list[dict]],
    argument: dict,
    call: dict,
    control_flow: dict,
) -> list[dict] | None:
    call_constraints = branch_constraints(call, control_flow)

    if _contains(argument, source):
        source_constraints = branch_constraints(
            source,
            control_flow,
        )

        if constraints_compatible(
            source_constraints,
            call_constraints,
        ):
            return [
                {
                    "kind": "SOURCE",
                    "target": source["target"],
                    "line": source["start_line"],
                },
                {
                    "kind": "CALL_ARGUMENT",
                    "value": argument["text"],
                    "line": argument["start_line"],
                },
            ]

    for name, states in source_states.items():
        if not _mentions_identifier(argument["text"], name):
            continue

        for state in states:
            if state["last_position"] > _start_position(call):
                continue

            if not constraints_compatible(
                state["constraints"],
                call_constraints,
            ):
                continue

            return [
                *state["trace"],
                {
                    "kind": "CALL_ARGUMENT",
                    "value": argument["text"],
                    "via": name,
                    "line": argument["start_line"],
                },
            ]

    return None


def _state_reaching_call(
    states: dict[str, list[dict]],
    call: dict | None,
    control_flow: dict,
) -> tuple[str, dict] | None:
    if call is None:
        return None

    call_constraints = branch_constraints(call, control_flow)
    arguments = call.get("argument_values", [])

    for name, name_states in states.items():
        if not any(
            _mentions_identifier(argument["text"], name)
            for argument in arguments
        ):
            continue

        for state in name_states:
            if state["last_position"] > _start_position(call):
                continue

            if constraints_compatible(
                state["constraints"],
                call_constraints,
            ):
                return name, state

    return None


def _find_relationship_call(
    relationship: dict,
    caller: dict,
    calls: list,
) -> dict | None:
    candidates = [
        call
        for call in calls
        if call["target"] == relationship["call_target"]
        and call["start_line"] == relationship["line"]
        and _contains(caller, call)
    ]
    return candidates[0] if len(candidates) == 1 else None


def _matching_call(observation: dict, calls: list) -> dict | None:
    return next(
        (
            call
            for call in calls
            if call["target"] == observation["target"]
            and _start_position(call)
            == _start_position(observation)
            and _end_position(call)
            == _end_position(observation)
        ),
        None,
    )


def _argument_at(call: dict, index: int) -> dict | None:
    arguments = call.get("argument_values", [])
    return arguments[index] if index < len(arguments) else None


def _items_in_scope(
    items: list,
    scope: dict,
    symbols: list,
) -> list:
    return [
        item
        for item in items
        if _find_scope(item, symbols) is scope
    ]


def _find_scope(item: dict, symbols: list) -> dict | None:
    candidates = [
        symbol
        for symbol in symbols
        if _contains(symbol, item)
    ]
    return (
        min(
            candidates,
            key=lambda symbol: (
                symbol["end_line"] - symbol["start_line"],
                symbol["end_column"]
                - symbol["start_column"],
            ),
        )
        if candidates
        else None
    )


def _control_steps(controls: list, location: dict) -> list[dict]:
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


def _assignment_step(assignment: dict) -> dict:
    return {
        "kind": "ASSIGNMENT",
        "target": assignment["target"],
        "value": assignment["value"],
        "line": assignment["start_line"],
    }


def _endpoint(item: dict) -> dict:
    return {
        key: item[key]
        for key in (
            "rule_id",
            "kind",
            "category",
            "target",
            "start_line",
            "end_line",
            "start_column",
            "end_column",
        )
    }


def _contains(outer: dict, inner: dict) -> bool:
    return (
        _start_position(outer) <= _start_position(inner)
        and _end_position(outer) >= _end_position(inner)
    )


def _start_position(item: dict) -> tuple[int, int]:
    return item["start_line"], item["start_column"]


def _end_position(item: dict) -> tuple[int, int]:
    return item["end_line"], item["end_column"]


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
