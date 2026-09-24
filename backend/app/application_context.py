from __future__ import annotations


SERVICE_TYPE_SUFFIXES = ("Service", "Repository", "Client")


def enrich_application_understanding(
    *,
    parsed: dict,
    semantics: dict,
    base: dict,
) -> dict:
    understanding = dict(base)
    dependencies = _dependencies(parsed)
    services = _services(parsed)
    database_operations = _database_operations(semantics)
    security_controls = _security_controls(base, semantics)
    understanding.update(
        {
            "dependencies": dependencies,
            "services": services,
            "database_operations": database_operations,
            "security_context": {
                "controls": security_controls,
                "claims": {
                    "control_presence_is_effectiveness_proof": False,
                    "authorization_coverage_proven": False,
                    "ownership_enforcement_proven": False,
                },
            },
        }
    )
    understanding["counts"] = {
        **base["counts"],
        "dependencies": len(dependencies),
        "services": len(services),
        "database_operations": len(database_operations),
        "security_controls": len(security_controls),
    }
    return understanding


def _dependencies(parsed: dict) -> list[dict]:
    return [
        {
            "module": item.get("module"),
            "statement_kind": item.get("kind"),
            "status": "OBSERVED",
            "origin": "UNRESOLVED",
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "start_column": item["start_column"],
            "end_column": item["end_column"],
        }
        for item in parsed.get("imports", [])
    ]


def _services(parsed: dict) -> list[dict]:
    class_names = [item["name"] for item in parsed.get("classes", [])]
    import_text = "\n".join(
        item.get("statement", "")
        for item in parsed.get("imports", [])
    )
    services = []
    for assignment in parsed.get("assignments", []):
        value_location = assignment.get("value_location", assignment)
        calls = [
            call
            for call in parsed.get("calls", [])
            if _contains(value_location, call)
        ]
        if len(calls) != 1:
            continue
        service_type = calls[0]["target"].rsplit(".", 1)[-1]
        if not service_type.endswith(SERVICE_TYPE_SUFFIXES):
            continue
        local_matches = [name for name in class_names if name == service_type]
        if len(local_matches) == 1:
            resolution = "RESOLVED_LOCAL_CLASS"
        elif service_type in import_text:
            resolution = "CANDIDATE_IMPORTED_TYPE"
        else:
            resolution = "CANDIDATE_UNRESOLVED_TYPE"
        services.append(
            {
                "variable": assignment["target"],
                "type": service_type,
                "constructor_target": calls[0]["target"],
                "status": (
                    "RESOLVED"
                    if resolution == "RESOLVED_LOCAL_CLASS"
                    else "CANDIDATE"
                ),
                "resolution": resolution,
                "start_line": assignment["start_line"],
                "end_line": assignment["end_line"],
                "start_column": assignment["start_column"],
                "end_column": assignment["end_column"],
            }
        )
    return services


def _database_operations(semantics: dict) -> list[dict]:
    return [
        {
            "target": item["target"],
            "operation": item["target"].rsplit(".", 1)[-1],
            "resource": "UNRESOLVED",
            "status": "CANDIDATE",
            "evidence_strength": item["evidence_strength"],
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "start_column": item["start_column"],
            "end_column": item["end_column"],
        }
        for item in semantics.get("sinks", [])
        if item["category"] == "sql_execution_candidate"
    ]


def _security_controls(base: dict, semantics: dict) -> list[dict]:
    framework_controls = [
        {**item, "source": "FRAMEWORK_DECORATOR"}
        for item in base.get("authentication_controls", [])
    ]
    semantic_controls = [
        {
            "kind": item["category"].upper(),
            "target": item["target"],
            "handler": None,
            "status": "OBSERVED",
            "effectiveness": "UNVERIFIED",
            "source": "CALL_SEMANTIC",
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "start_column": item["start_column"],
            "end_column": item["end_column"],
        }
        for item in semantics.get("security_controls", [])
    ]
    return framework_controls + semantic_controls


def _contains(outer: dict, inner: dict) -> bool:
    return (
        (outer["start_line"], outer["start_column"])
        <= (inner["start_line"], inner["start_column"])
        and (outer["end_line"], outer["end_column"])
        >= (inner["end_line"], inner["end_column"])
    )
