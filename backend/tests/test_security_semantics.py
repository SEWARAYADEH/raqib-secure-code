from app.parser_engine import parse_source
from app.security_semantics import (
    MATCH_EXACT,
    MATCH_SUFFIX,
    SEMANTIC_SINK,
    SEMANTIC_SOURCE,
    classify_security_semantics,
)


def test_flask_request_source_is_detected():
    source = """
from flask import request

def get_user():
    user_id = request.args.get("id")
    return user_id
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    result = classify_security_semantics(
        parsed
    )

    assert result["counts"]["sources"] == 1

    observation = result["sources"][0]

    assert observation["kind"] == SEMANTIC_SOURCE

    assert (
        observation["category"]
        == "http_query_input"
    )

    assert observation["target"] == (
        "request.args.get"
    )

    assert observation["match_type"] == (
        MATCH_EXACT
    )

    assert observation[
        "evidence_strength"
    ] == "DIRECT"


def test_os_system_is_sensitive_sink():
    source = """
import os

def run_command(command):
    os.system(command)
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    result = classify_security_semantics(
        parsed
    )

    assert result["counts"]["sinks"] == 1

    sink = result["sinks"][0]

    assert sink["kind"] == SEMANTIC_SINK

    assert sink["category"] == (
        "os_command_execution"
    )

    assert sink["target"] == "os.system"

    assert sink["evidence_strength"] == (
        "DIRECT"
    )


def test_execute_suffix_is_only_heuristic():
    source = """
def load_user(database, user_id):
    return database.execute(user_id)
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    result = classify_security_semantics(
        parsed
    )

    assert result["counts"]["sinks"] == 1

    sink = result["sinks"][0]

    assert sink["category"] == (
        "sql_execution_candidate"
    )

    assert sink["match_type"] == (
        MATCH_SUFFIX
    )

    assert sink["evidence_strength"] == (
        "HEURISTIC"
    )


def test_safe_unrelated_call_is_not_classified():
    source = """
def format_name(name):
    return name.strip()
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    result = classify_security_semantics(
        parsed
    )

    assert result["observations"] == []

    assert result["counts"] == {
        "sources": 0,
        "sinks": 0,
        "security_controls": 0,
    }


def test_javascript_eval_is_detected():
    source = """
function runCode(value) {
    return eval(value);
}
""".strip()

    parsed = parse_source(
        source,
        "JavaScript",
    )

    result = classify_security_semantics(
        parsed
    )

    assert result["counts"]["sinks"] == 1

    sink = result["sinks"][0]

    assert sink["target"] == "eval"

    assert sink["category"] == (
        "dynamic_code_execution"
    )


def test_semantic_observation_is_not_a_finding():
    source = """
from flask import request

def example():
    value = request.args.get("value")
    return value
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    result = classify_security_semantics(
        parsed
    )

    observation = result["sources"][0]

    assert "vulnerability" not in observation

    assert "severity" not in observation

    assert "cwe" not in observation


def test_security_control_is_observed_without_safety_claim():
    source = '''
import shlex

def normalize(value):
    return shlex.quote(value)
'''.strip()

    parsed = parse_source(source, "Python")
    result = classify_security_semantics(parsed)

    assert result["counts"]["security_controls"] == 1
    control = result["security_controls"][0]
    assert control["kind"] == "SECURITY_CONTROL"
    assert control["category"] == "command_argument_escaping"
    assert "safe" not in control
    assert "vulnerability" not in control
