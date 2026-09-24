from __future__ import annotations


HTTP_METHODS = {
    "delete": "DELETE",
    "get": "GET",
    "patch": "PATCH",
    "post": "POST",
    "put": "PUT",
}

AUTH_DECORATOR_CANDIDATES = {
    "auth_required",
    "jwt_required",
    "login_required",
    "permission_required",
    "roles_required",
}

AUTHORIZATION_DECORATORS = {
    "permission_required",
    "roles_required",
}


def understand_frameworks(parsed: dict) -> dict:
    frameworks = _detect_frameworks(parsed)
    routes = _extract_routes(parsed)
    auth_controls = _extract_auth_controls(parsed)
    categories = {item["category"] for item in frameworks}

    if "WEB_API" in categories and "FRONTEND_UI" in categories:
        project_role = "FULL_STACK_COMPONENT"
    elif "WEB_API" in categories:
        project_role = "WEB_API_COMPONENT"
    elif "FRONTEND_UI" in categories:
        project_role = "FRONTEND_COMPONENT"
    else:
        project_role = "UNKNOWN_COMPONENT"

    return {
        "language": parsed.get("language"),
        "project_role": project_role,
        "frameworks": frameworks,
        "routes": routes,
        "authentication_controls": auth_controls,
        "counts": {
            "frameworks": len(frameworks),
            "routes": len(routes),
            "authentication_controls": len(auth_controls),
        },
        "claims": {
            "frameworks_require_code_evidence": True,
            "authentication_effectiveness_proven": False,
        },
    }


def _detect_frameworks(parsed: dict) -> list[dict]:
    import_text = "\n".join(
        item.get("statement", "").lower()
        for item in parsed.get("imports", [])
    )
    call_targets = {
        item.get("target", "")
        for item in parsed.get("calls", [])
    }
    decorator_targets = {
        item.get("target", "")
        for item in parsed.get("decorators", [])
    }
    matches = []

    rules = [
        {
            "name": "Flask",
            "category": "WEB_API",
            "import_tokens": ("import flask", "from flask"),
            "call_targets": {"Flask"},
            "decorator_suffixes": (
                ".route",
                ".get",
                ".post",
                ".put",
                ".patch",
                ".delete",
            ),
        },
        {
            "name": "React",
            "category": "FRONTEND_UI",
            "import_tokens": (
                "from 'react'",
                'from "react"',
                "from 'react/",
                'from "react/',
            ),
            "call_targets": {"createRoot", "React.createElement"},
            "decorator_suffixes": (),
        },
        {
            "name": "Express",
            "category": "WEB_API",
            "import_tokens": (
                "from 'express'",
                'from "express"',
                "require('express')",
                'require("express")',
            ),
            "call_targets": {"express"},
            "decorator_suffixes": (),
        },
    ]

    for rule in rules:
        evidence = []

        if any(
            token in import_text
            for token in rule["import_tokens"]
        ):
            evidence.append("IMPORT")

        if call_targets & rule["call_targets"]:
            evidence.append("CALL")

        if any(
            target.endswith(rule["decorator_suffixes"])
            for target in decorator_targets
        ):
            evidence.append("DECORATOR")

        if evidence:
            matches.append(
                {
                    "name": rule["name"],
                    "category": rule["category"],
                    "status": (
                        "CORROBORATED"
                        if len(evidence) > 1
                        else "CANDIDATE"
                    ),
                    "evidence": evidence,
                }
            )

    return matches


def _extract_routes(parsed: dict) -> list[dict]:
    if parsed.get("language") == "Python":
        return _extract_python_routes(parsed)

    if parsed.get("language") in {
        "JavaScript",
        "JavaScript JSX",
    }:
        return _extract_javascript_routes(parsed)

    return []


def _extract_python_routes(parsed: dict) -> list[dict]:
    routes = []
    functions = parsed.get("functions", [])

    for decorator in parsed.get("decorators", []):
        method_name = decorator["target"].rsplit(".", 1)[-1]

        if method_name not in {*HTTP_METHODS, "route"}:
            continue

        arguments = decorator.get("argument_values", [])
        path = _string_literal(arguments[0]["text"]) if arguments else None
        handler = _function_at_definition(
            functions,
            decorator["definition_location"],
        )

        routes.append(
            {
                "framework": "Flask",
                "path": path,
                "methods": (
                    [HTTP_METHODS[method_name]]
                    if method_name in HTTP_METHODS
                    else ["UNRESOLVED"]
                ),
                "handler": (
                    handler["name"] if handler else None
                ),
                "status": (
                    "RESOLVED"
                    if path and handler
                    else "PARTIAL"
                ),
                "start_line": decorator["start_line"],
                "end_line": decorator["end_line"],
                "start_column": decorator["start_column"],
                "end_column": decorator["end_column"],
            }
        )

    return routes


def _extract_javascript_routes(parsed: dict) -> list[dict]:
    routes = []

    for call in parsed.get("calls", []):
        parts = call["target"].rsplit(".", 1)

        if len(parts) != 2 or parts[1] not in HTTP_METHODS:
            continue

        owner, method_name = parts

        if owner not in {"app", "router"}:
            continue

        arguments = call.get("argument_values", [])
        path = _string_literal(arguments[0]["text"]) if arguments else None
        handler = arguments[1]["text"] if len(arguments) > 1 else None
        routes.append(
            {
                "framework": "Express",
                "path": path,
                "methods": [HTTP_METHODS[method_name]],
                "handler": handler,
                "status": (
                    "RESOLVED"
                    if path and handler
                    else "PARTIAL"
                ),
                "start_line": call["start_line"],
                "end_line": call["end_line"],
                "start_column": call["start_column"],
                "end_column": call["end_column"],
            }
        )

    return routes


def _extract_auth_controls(parsed: dict) -> list[dict]:
    controls = []

    for decorator in parsed.get("decorators", []):
        name = decorator["target"].rsplit(".", 1)[-1]

        if name not in AUTH_DECORATOR_CANDIDATES:
            continue

        handler = _function_at_definition(
            parsed.get("functions", []),
            decorator["definition_location"],
        )
        controls.append(
            {
                "kind": (
                    "AUTHORIZATION_CONTROL"
                    if name in AUTHORIZATION_DECORATORS
                    else "AUTHENTICATION_CONTROL"
                ),
                "target": decorator["target"],
                "handler": handler["name"] if handler else None,
                "status": "OBSERVED",
                "effectiveness": "UNVERIFIED",
                "start_line": decorator["start_line"],
                "end_line": decorator["end_line"],
                "start_column": decorator["start_column"],
                "end_column": decorator["end_column"],
            }
        )

    return controls


def _function_at_definition(
    functions: list,
    location: dict,
) -> dict | None:
    matches = [
        item
        for item in functions
        if all(
            item[key] == location[key]
            for key in (
                "start_line",
                "end_line",
                "start_column",
                "end_column",
            )
        )
    ]
    return matches[0] if len(matches) == 1 else None


def _string_literal(value: str) -> str | None:
    if len(value) < 2 or value[0] not in {"'", '"', "`"}:
        return None

    if value[-1] != value[0]:
        return None

    return value[1:-1]
