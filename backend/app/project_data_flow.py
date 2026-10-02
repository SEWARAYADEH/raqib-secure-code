"""One-boundary, evidence-only source-to-sink flow across resolved imports."""

from __future__ import annotations

import re


def build_cross_file_data_flow(
    file_results: list[dict], cross_file_calls: list[dict]
) -> list[dict]:
    files = {item["artifact"]["relative_path"]: item for item in file_results}
    paths = []
    for relationship in cross_file_calls:
        caller_file = files[relationship["source_file"]]
        callee_file = files[relationship["target_file"]]
        caller_symbol = _symbol(caller_file, relationship["caller_id"])
        callee_symbol = _symbol(callee_file, relationship["callee_id"])
        if caller_symbol is None or callee_symbol is None:
            continue
        calls = [
            item for item in caller_file["structure"]["calls"]
            if item["start_line"] == relationship["call_line"]
            and item["target"] == relationship["call_target"]
        ]
        functions = [
            item for item in callee_file["structure"]["functions"]
            if item["name"] == callee_symbol["name"]
            and item["start_line"] == callee_symbol["start_line"]
        ]
        if len(calls) != 1 or len(functions) != 1:
            continue
        for source in caller_file["security_semantics"]["sources"]:
            if not _contains(caller_symbol, source):
                continue
            caller_taint, caller_trace = _taint_from_source(caller_file, caller_symbol, source)
            for index, argument in enumerate(calls[0].get("argument_values", [])):
                if index >= len(functions[0].get("parameter_values", [])):
                    continue
                if not (
                    _contains(argument, source)
                    or any(_mentions(argument["text"], name) for name in caller_taint)
                ):
                    continue
                parameter = functions[0]["parameter_values"][index]["text"]
                if not _identifier(parameter):
                    continue
                callee_taint, callee_trace = _taint_from_parameter(
                    callee_file, callee_symbol, parameter
                )
                for sink in callee_file["security_semantics"]["sinks"]:
                    if not _contains(callee_symbol, sink):
                        continue
                    sink_calls = [
                        item for item in callee_file["structure"]["calls"]
                        if item["target"] == sink["target"]
                        and item["start_line"] == sink["start_line"]
                    ]
                    matched_name = (
                        _call_tainted_name(sink_calls[0], callee_taint)
                        if len(sink_calls) == 1 else None
                    )
                    if matched_name is None:
                        continue
                    paths.append({
                        "kind": "CROSS_FILE_SOURCE_TO_SENSITIVE_SINK_PATH",
                        "status": "OBSERVED",
                        "source_file": relationship["source_file"],
                        "target_file": relationship["target_file"],
                        "source": source,
                        "sink": sink,
                        "caller": relationship["caller"],
                        "callee": relationship["callee"],
                        "scope": {
                            "function": relationship["callee"],
                            "caller": relationship["caller"],
                            "callee": relationship["callee"],
                            "start_line": callee_symbol["start_line"],
                            "end_line": callee_symbol["end_line"],
                        },
                        "resolution": relationship["resolution"],
                        "argument_index": index,
                        "trace": [
                            {"kind": "SOURCE", "file": relationship["source_file"],
                             "target": source["target"], "line": source["start_line"]},
                            *caller_trace,
                            {"kind": "CALL_ARGUMENT", "file": relationship["source_file"],
                             "target": calls[0]["target"], "line": calls[0]["start_line"],
                             "argument_index": index},
                            {"kind": "CALL_BOUNDARY", "resolution": relationship["resolution"]},
                            {"kind": "PARAMETER", "file": relationship["target_file"],
                             "target": parameter, "line": functions[0]["start_line"]},
                            *callee_trace,
                            {"kind": "SINK", "file": relationship["target_file"],
                             "target": sink["target"], "line": sink["start_line"],
                             "via": matched_name},
                        ],
                        "evidence_strength": (
                            "DIRECT" if source["evidence_strength"] == "DIRECT"
                            and sink["evidence_strength"] == "DIRECT" else "HEURISTIC"
                        ),
                        "runtime_verified": False,
                    })
    return paths


def _symbol(result: dict, symbol_id: str) -> dict | None:
    matches = [item for item in result["relationships"]["symbols"] if item["id"] == symbol_id]
    return matches[0] if len(matches) == 1 else None


def _taint_from_source(result: dict, scope: dict, source: dict) -> tuple[set[str], list[dict]]:
    tainted = set()
    trace = []
    for item in sorted(result["structure"]["assignments"], key=lambda value: value["start_line"]):
        if not _contains(scope, item) or item["start_line"] < source["start_line"]:
            continue
        value_location = item.get("value_location") or item
        if _contains(value_location, source) or any(_mentions(item["value"], name) for name in tainted):
            if _identifier(item["target"]):
                tainted.add(item["target"])
                trace.append({"kind": "ASSIGNMENT", "file": result["artifact"]["relative_path"],
                              "target": item["target"], "value": item["value"],
                              "line": item["start_line"]})
    return tainted, trace


def _taint_from_parameter(result: dict, scope: dict, parameter: str) -> tuple[set[str], list[dict]]:
    tainted = {parameter}
    trace = []
    for item in sorted(result["structure"]["assignments"], key=lambda value: value["start_line"]):
        if _contains(scope, item) and any(_mentions(item["value"], name) for name in tainted):
            if _identifier(item["target"]):
                tainted.add(item["target"])
                trace.append({"kind": "ASSIGNMENT", "file": result["artifact"]["relative_path"],
                              "target": item["target"], "value": item["value"],
                              "line": item["start_line"]})
    return tainted, trace


def _call_tainted_name(call: dict, names: set[str]) -> str | None:
    texts = [item.get("text", "") for item in call.get("argument_values", [])]
    if "." in call.get("target", ""):
        texts.append(call["target"].rsplit(".", 1)[0])
    return next(
        (name for name in sorted(names) if any(_mentions(text, name) for text in texts)),
        None,
    )


def _contains(outer: dict, inner: dict) -> bool:
    return ((outer["start_line"], outer["start_column"])
            <= (inner["start_line"], inner["start_column"])
            and (outer["end_line"], outer["end_column"])
            >= (inner["end_line"], inner["end_column"]))


def _identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value))


def _mentions(text: str, name: str) -> bool:
    return bool(re.search(rf"(?<![A-Za-z0-9_$]){re.escape(name)}(?![A-Za-z0-9_$])", text))
