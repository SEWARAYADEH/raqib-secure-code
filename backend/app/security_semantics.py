from __future__ import annotations


SEMANTIC_SOURCE = "SOURCE"
SEMANTIC_SINK = "SINK"
SEMANTIC_CONTROL = "SECURITY_CONTROL"

MATCH_EXACT = "EXACT"
MATCH_SUFFIX = "SUFFIX"


SEMANTIC_RULES = {
    "Python": [
        {
            "id": "PY-SRC-FLASK-QUERY",
            "kind": SEMANTIC_SOURCE,
            "category": "http_query_input",
            "targets": {
                "request.args.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-FLASK-FORM",
            "kind": SEMANTIC_SOURCE,
            "category": "http_form_input",
            "targets": {
                "request.form.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-FLASK-VALUES",
            "kind": SEMANTIC_SOURCE,
            "category": "http_request_input",
            "targets": {
                "request.values.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-FLASK-HEADER",
            "kind": SEMANTIC_SOURCE,
            "category": "http_header_input",
            "targets": {
                "request.headers.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-FLASK-COOKIE",
            "kind": SEMANTIC_SOURCE,
            "category": "http_cookie_input",
            "targets": {
                "request.cookies.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-FLASK-JSON",
            "kind": SEMANTIC_SOURCE,
            "category": "http_json_input",
            "targets": {
                "request.get_json",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-EVAL",
            "kind": SEMANTIC_SINK,
            "category": "dynamic_code_execution",
            "targets": {
                "eval",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-EXEC",
            "kind": SEMANTIC_SINK,
            "category": "dynamic_code_execution",
            "targets": {
                "exec",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-OS-SYSTEM",
            "kind": SEMANTIC_SINK,
            "category": "os_command_execution",
            "targets": {
                "os.system",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-SUBPROCESS",
            "kind": SEMANTIC_SINK,
            "category": "process_execution",
            "targets": {
                "subprocess.run",
                "subprocess.Popen",
                "subprocess.call",
                "subprocess.check_call",
                "subprocess.check_output",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-SQL-EXECUTE-CANDIDATE",
            "kind": SEMANTIC_SINK,
            "category": "sql_execution_candidate",
            "targets": {
                ".execute",
                ".executemany",
            },
            "match": MATCH_SUFFIX,
        },
        {
            "id": "PY-CTRL-SHLEX-QUOTE",
            "kind": SEMANTIC_CONTROL,
            "category": "command_argument_escaping",
            "targets": {"shlex.quote"},
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-CTRL-HTML-ESCAPE",
            "kind": SEMANTIC_CONTROL,
            "category": "output_encoding",
            "targets": {
                "html.escape",
                "markupsafe.escape",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-CTRL-PASSWORD-CHECK",
            "kind": SEMANTIC_CONTROL,
            "category": "credential_verification",
            "targets": {
                "check_password_hash",
                "werkzeug.security.check_password_hash",
            },
            "match": MATCH_EXACT,
        },
    ],
    "JavaScript": [
        {
            "id": "JS-SRC-HTTP-HEADER",
            "kind": SEMANTIC_SOURCE,
            "category": "http_header_input",
            "targets": {
                "req.get",
                "request.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-SINK-EVAL",
            "kind": SEMANTIC_SINK,
            "category": "dynamic_code_execution",
            "targets": {
                "eval",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-SINK-FUNCTION-CONSTRUCTOR",
            "kind": SEMANTIC_SINK,
            "category": "dynamic_code_execution",
            "targets": {
                "Function",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-SINK-CHILD-PROCESS",
            "kind": SEMANTIC_SINK,
            "category": "process_execution",
            "targets": {
                "child_process.exec",
                "child_process.execSync",
                "child_process.spawn",
                "child_process.spawnSync",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-SINK-SQL-QUERY-CANDIDATE",
            "kind": SEMANTIC_SINK,
            "category": "sql_execution_candidate",
            "targets": {
                ".query",
                ".execute",
            },
            "match": MATCH_SUFFIX,
        },
        {
            "id": "JS-CTRL-URI-ENCODE",
            "kind": SEMANTIC_CONTROL,
            "category": "uri_component_encoding",
            "targets": {"encodeURIComponent"},
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-CTRL-VALIDATOR-ESCAPE",
            "kind": SEMANTIC_CONTROL,
            "category": "output_encoding",
            "targets": {"validator.escape"},
            "match": MATCH_EXACT,
        },
    ],
}


def classify_security_semantics(
    parsed: dict,
) -> dict:
    language = parsed.get("language")

    rules = SEMANTIC_RULES.get(
        language,
        [],
    )

    observations = []

    for call in parsed.get("calls", []):
        target = call.get("target", "").strip()

        if not target:
            continue

        matches = _match_target(
            target,
            rules,
        )

        for rule in matches:
            observations.append(
                _build_observation(
                    call=call,
                    target=target,
                    rule=rule,
                )
            )

    sources = [
        item
        for item in observations
        if item["kind"] == SEMANTIC_SOURCE
    ]

    sinks = [
        item
        for item in observations
        if item["kind"] == SEMANTIC_SINK
    ]

    controls = [
        item
        for item in observations
        if item["kind"] == SEMANTIC_CONTROL
    ]

    return {
        "language": language,
        "observations": observations,
        "sources": sources,
        "sinks": sinks,
        "security_controls": controls,
        "counts": {
            "sources": len(sources),
            "sinks": len(sinks),
            "security_controls": len(controls),
        },
    }


def _match_target(
    target: str,
    rules: list,
) -> list:
    matches = []

    for rule in rules:
        match_type = rule["match"]

        if match_type == MATCH_EXACT:
            if target in rule["targets"]:
                matches.append(rule)

        elif match_type == MATCH_SUFFIX:
            if any(
                target.endswith(suffix)
                for suffix in rule["targets"]
            ):
                matches.append(rule)

    return matches


def _build_observation(
    *,
    call: dict,
    target: str,
    rule: dict,
) -> dict:
    return {
        "rule_id": rule["id"],
        "kind": rule["kind"],
        "category": rule["category"],
        "target": target,
        "match_type": rule["match"],
        "evidence_strength": (
            "DIRECT"
            if rule["match"] == MATCH_EXACT
            else "HEURISTIC"
        ),
        "start_line": call["start_line"],
        "end_line": call["end_line"],
        "start_column": call["start_column"],
        "end_column": call["end_column"],
    }
