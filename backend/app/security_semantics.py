from __future__ import annotations

import re


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
                "request.json.get",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SRC-HTTP-BODY",
            "kind": SEMANTIC_SOURCE,
            "category": "http_body_input",
            "targets": {"request.get_data"},
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
                "os.popen",
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
                "subprocess.getoutput",
                "subprocess.getstatusoutput",
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
            "id": "PY-SINK-FILESYSTEM",
            "kind": SEMANTIC_SINK,
            "category": "filesystem_path_operation",
            "targets": {
                "open", "send_file", "os.open", "os.remove", "os.unlink",
                "os.rename", "os.replace", "shutil.copy", "shutil.move",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-SINK-PATHLIB",
            "kind": SEMANTIC_SINK,
            "category": "filesystem_path_operation",
            "targets": {
                ".open", ".read_text", ".read_bytes", ".write_text",
                ".write_bytes", ".unlink",
            },
            "match": MATCH_SUFFIX,
        },
        {
            "id": "PY-SINK-OBJECT-ACCESS",
            "kind": SEMANTIC_SINK,
            "category": "authorization_sensitive_object_access",
            "targets": {".query.get", ".get_or_404", ".filter_by"},
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
        {
            "id": "PY-CTRL-PATH-NORMALIZATION",
            "kind": SEMANTIC_CONTROL,
            "category": "path_normalization",
            "targets": {"os.path.abspath", "os.path.realpath", "Path.resolve", ".resolve"},
            "match": MATCH_SUFFIX,
        },
        {
            "id": "PY-CTRL-PATH-CONTAINMENT",
            "kind": SEMANTIC_CONTROL,
            "category": "path_containment_check",
            "targets": {"os.path.commonpath", ".is_relative_to"},
            "match": MATCH_SUFFIX,
        },
        {
            "id": "PY-CTRL-FILENAME",
            "kind": SEMANTIC_CONTROL,
            "category": "filename_sanitization",
            "targets": {"secure_filename", "werkzeug.utils.secure_filename"},
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-CTRL-AUTHENTICATION",
            "kind": SEMANTIC_CONTROL,
            "category": "authentication_check",
            "targets": {"authenticate", "login_user", "verify_token"},
            "match": MATCH_EXACT,
        },
        {
            "id": "PY-CTRL-AUTHORIZATION",
            "kind": SEMANTIC_CONTROL,
            "category": "authorization_check",
            "targets": {"authorize", "check_permission", "has_permission"},
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
            "id": "JS-SINK-FILESYSTEM",
            "kind": SEMANTIC_SINK,
            "category": "filesystem_path_operation",
            "targets": {
                "fs.readFile", "fs.readFileSync", "fs.writeFile",
                "fs.writeFileSync", "fs.unlink", "fs.rename", "res.sendFile",
            },
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-SINK-DOM-HTML",
            "kind": SEMANTIC_SINK,
            "category": "html_dom_rendering",
            "targets": {"res.send", "res.write", "document.write", ".insertAdjacentHTML"},
            "match": MATCH_SUFFIX,
        },
        {
            "id": "JS-SINK-OBJECT-ACCESS",
            "kind": SEMANTIC_SINK,
            "category": "authorization_sensitive_object_access",
            "targets": {".findById", ".findOne", ".findUnique"},
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
        {
            "id": "JS-CTRL-DOMPURIFY",
            "kind": SEMANTIC_CONTROL,
            "category": "html_sanitization",
            "targets": {"DOMPurify.sanitize"},
            "match": MATCH_EXACT,
        },
        {
            "id": "JS-CTRL-PATH-NORMALIZATION",
            "kind": SEMANTIC_CONTROL,
            "category": "path_normalization",
            "targets": {"path.normalize", "path.resolve"},
            "match": MATCH_EXACT,
        },
    ],
}


def classify_security_semantics(
    parsed: dict,
) -> dict:
    language = parsed.get("language")

    rules = SEMANTIC_RULES.get(
        "JavaScript" if language == "JavaScript JSX" else language,
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

    observations.extend(_property_sources(parsed))
    observations.extend(_route_parameter_sources(parsed))
    observations.extend(_structural_controls(parsed))

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


_PROPERTY_SOURCE_PATTERNS = {
    "Python": (
        (re.compile(r"\brequest\.(?:args|query_params)\s*\["), "http_query_input"),
        (re.compile(r"\brequest\.form\s*\["), "http_form_input"),
        (re.compile(r"\brequest\.(?:json|body)\s*\["), "http_json_input"),
        (re.compile(r"\brequest\.headers\s*\["), "http_header_input"),
        (re.compile(r"\brequest\.cookies\s*\["), "http_cookie_input"),
    ),
    "JavaScript": (
        (re.compile(r"\b(?:req|request)\.query(?:\.|\[)"), "http_query_input"),
        (re.compile(r"\b(?:req|request)\.params(?:\.|\[)"), "http_path_input"),
        (re.compile(r"\b(?:req|request)\.body(?:\.|\[)"), "http_body_input"),
        (re.compile(r"\b(?:req|request)\.headers(?:\.|\[)"), "http_header_input"),
        (re.compile(r"\b(?:req|request)\.cookies(?:\.|\[)"), "http_cookie_input"),
    ),
}


def _property_sources(parsed: dict) -> list[dict]:
    language = parsed.get("language")
    patterns = _PROPERTY_SOURCE_PATTERNS.get(
        "JavaScript" if language == "JavaScript JSX" else language, ()
    )
    observations = []
    for assignment in parsed.get("assignments", []):
        value = assignment.get("value", "")
        location = assignment.get("value_location") or assignment
        matches = [(pattern, category) for pattern, category in patterns if pattern.search(value)]
        if len(matches) != 1:
            continue
        observations.append({
            "rule_id": f"PROPERTY-SOURCE-{matches[0][1].upper()}",
            "kind": SEMANTIC_SOURCE,
            "category": matches[0][1],
            "target": value,
            "match_type": "STRUCTURAL_PATTERN",
            "evidence_strength": "DIRECT",
            **{key: location[key] for key in (
                "start_line", "end_line", "start_column", "end_column"
            )},
        })
    return observations


def _route_parameter_sources(parsed: dict) -> list[dict]:
    if parsed.get("language") != "Python":
        return []
    observations = []
    for decorator in parsed.get("decorators", []):
        target = decorator.get("target", "").rsplit(".", 1)[-1]
        arguments = decorator.get("argument_values", [])
        if target not in {"route", "get", "post", "put", "patch", "delete"} or not arguments:
            continue
        literal = arguments[0].get("text", "")
        if len(literal) < 2 or literal[0] not in {"'", '"'} or literal[-1] != literal[0]:
            continue
        path = literal[1:-1]
        names = set(re.findall(r"<(?:(?:[^:>]+):)?([A-Za-z_]\w*)>", path))
        names.update(re.findall(r"{([A-Za-z_]\w*)}", path))
        functions = [
            function for function in parsed.get("functions", [])
            if function["start_line"] == decorator["definition_location"]["start_line"]
            and function["start_column"] == decorator["definition_location"]["start_column"]
        ]
        if len(functions) != 1:
            continue
        for parameter in functions[0].get("parameter_values", []):
            binding = parameter["text"].split(":", 1)[0].split("=", 1)[0].strip()
            if binding not in names:
                continue
            observations.append({
                "rule_id": "PY-SRC-ROUTE-PARAMETER",
                "kind": SEMANTIC_SOURCE,
                "category": "http_path_input",
                "target": binding,
                "binding": binding,
                "match_type": "ROUTE_PARAMETER_BINDING",
                "evidence_strength": "DIRECT",
                **{key: parameter[key] for key in (
                    "start_line", "end_line", "start_column", "end_column"
                )},
            })
    return observations


def _structural_controls(parsed: dict) -> list[dict]:
    observations = []
    for region in parsed.get("control_regions", []):
        condition = region.get("condition") or ""
        categories = []
        if (
            "is_relative_to(" in condition
            or "commonpath(" in condition
            or re.search(
                r"\b[A-Za-z_][A-Za-z0-9_]*\s+not\s+in\s+"
                r"[A-Za-z_][A-Za-z0-9_]*\.parents\b",
                condition,
            )
        ):
            categories.append("path_containment_check")
        if re.search(r"\b(?:current_user|user)\.is_authenticated\b", condition):
            categories.append("authentication_check")
        if re.search(r"\b(?:owner_id|user_id)\s*==|==\s*(?:owner_id|user_id)\b", condition):
            categories.append("ownership_check")
        if re.search(r"\b[A-Za-z_$][A-Za-z0-9_$]*\s+in\s+[A-Za-z_$][A-Za-z0-9_$]*", condition):
            categories.append("allowlist_membership_check")
        for category in categories:
            location = {
                key: region[key] for key in (
                    "start_line", "end_line", "start_column", "end_column"
                )
            }
            if (
                category == "path_containment_check"
                and " not in " in condition
                and _region_terminates(parsed, region)
            ):
                functions = [
                    item for item in parsed.get("functions", [])
                    if _contains_location(item, region)
                ]
                if len(functions) == 1:
                    location["start_line"] = region["end_line"]
                    location["start_column"] = 0
                    location["end_line"] = functions[0]["end_line"]
                    location["end_column"] = functions[0]["end_column"]
            observations.append({
                "rule_id": f"STRUCTURAL-CONTROL-{category.upper()}",
                "kind": SEMANTIC_CONTROL,
                "category": category,
                "target": condition,
                "match_type": "STRUCTURAL_PATTERN",
                "evidence_strength": "DIRECT",
                **location,
            })
    return observations


def _region_terminates(parsed: dict, region: dict) -> bool:
    return any(
        _contains_location(region, call)
        and call.get("target") in {"abort", "raise_for_status"}
        for call in parsed.get("calls", [])
    ) or any(
        _contains_location(region, item)
        for item in parsed.get("returns", [])
    )


def _contains_location(outer: dict, inner: dict) -> bool:
    return (
        (outer["start_line"], outer["start_column"])
        <= (inner["start_line"], inner["start_column"])
        and (outer["end_line"], outer["end_column"])
        >= (inner["end_line"], inner["end_column"])
    )
