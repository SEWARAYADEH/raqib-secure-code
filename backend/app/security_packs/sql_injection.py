"""Distinguish input influencing SQL text from bound-parameter input."""

from __future__ import annotations

import ast
import re


QUERY_TEXT_INFLUENCE = "QUERY_TEXT_INFLUENCE_CANDIDATE"
NON_QUERY_ARGUMENT = "NON_QUERY_ARGUMENT_ONLY"
UNRESOLVED = "SQL_ARGUMENT_INFLUENCE_UNRESOLVED"
_SQL_SHAPE = re.compile(
    r"\b(?:SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|DROP|ALTER)\b",
    re.IGNORECASE,
)


def assess_sql_path(path: dict, parsed: dict) -> dict:
    """Assess only the observed path, without asserting DB-API behavior.

    The first positional argument of supported ``execute``/``query`` calls is
    treated as query text. Input found solely in later arguments is retained
    as an observation and does not become a SQL-injection candidate.
    """
    sink = path["sink"]
    calls = [
        call for call in parsed.get("calls", [])
        if call.get("target") == sink["target"]
        and call.get("start_line") == sink["start_line"]
        and call.get("start_column") == sink["start_column"]
    ]
    if len(calls) != 1:
        return _result(UNRESOLVED, "SINK_CALL_NOT_UNIQUE")
    arguments = calls[0].get("argument_values", [])
    if not arguments:
        return _result(UNRESOLVED, "QUERY_ARGUMENT_NOT_OBSERVED")

    query_argument = arguments[0]
    source = path["source"]
    if _is_static_string(query_argument.get("text", ""), parsed.get("language")):
        return _result(NON_QUERY_ARGUMENT, "QUERY_TEXT_IS_STATIC_LITERAL")
    if _contains(query_argument, source):
        return _query_candidate_or_unresolved(
            path, query_argument, "SOURCE_IN_QUERY_ARGUMENT"
        )

    sink_steps = [step for step in path.get("trace", []) if step["kind"] == "SINK"]
    variable = sink_steps[-1].get("via") if sink_steps else None
    if isinstance(variable, str) and _mentions_identifier(
        query_argument.get("text", ""), variable
    ):
        return _query_candidate_or_unresolved(
            path, query_argument, "TAINTED_VARIABLE_IN_QUERY_ARGUMENT"
        )

    if len(arguments) > 1 and (
        any(_contains(argument, source) for argument in arguments[1:])
        or isinstance(variable, str)
        and any(
            _mentions_identifier(argument.get("text", ""), variable)
            for argument in arguments[1:]
        )
    ):
        return _result(NON_QUERY_ARGUMENT, "INPUT_ONLY_IN_LATER_ARGUMENT")

    return _result(UNRESOLVED, "QUERY_ARGUMENT_INFLUENCE_NOT_ESTABLISHED")


def _is_static_string(text: str, language: str | None) -> bool:
    if language == "Python":
        try:
            return isinstance(ast.literal_eval(text), str)
        except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
            return False
    if language in {"JavaScript", "JavaScript JSX"}:
        if len(text) < 2 or text[0] not in {"'", '"', "`"} or text[-1] != text[0]:
            return False
        if text[0] == "`" and "${" in text:
            return False
        # A complete quoted token has no unescaped copy of its delimiter inside.
        escaped = False
        for character in text[1:-1]:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == text[0]:
                return False
        return not escaped
    return False


def _query_candidate_or_unresolved(
    path: dict, query_argument: dict, basis: str
) -> dict:
    evidence_texts = [query_argument.get("text", "")]
    evidence_texts.extend(
        step.get("value", "") for step in path.get("trace", [])
        if step.get("kind") == "ASSIGNMENT"
    )
    if any(
        _SQL_SHAPE.search(text) and any(quote in text for quote in ("'", '"', '`'))
        for text in evidence_texts
    ):
        return _result(QUERY_TEXT_INFLUENCE, basis)
    return _result(UNRESOLVED, "SQL_QUERY_SHAPE_NOT_ESTABLISHED")


def _contains(outer: dict, inner: dict) -> bool:
    return (
        (outer["start_line"], outer["start_column"])
        <= (inner["start_line"], inner["start_column"])
        and (outer["end_line"], outer["end_column"])
        >= (inner["end_line"], inner["end_column"])
    )


def _mentions_identifier(text: str, identifier: str) -> bool:
    return bool(re.search(
        rf"(?<![A-Za-z0-9_$]){re.escape(identifier)}(?![A-Za-z0-9_$])",
        text,
    ))


def _result(status: str, basis: str) -> dict:
    return {
        "pack": "SQL_INJECTION",
        "status": status,
        "basis": basis,
        "scope": "FIRST_POSITIONAL_QUERY_ARGUMENT_ONLY",
        "database_api_identity": "UNVERIFIED",
        "runtime_effectiveness_verified": False,
    }
