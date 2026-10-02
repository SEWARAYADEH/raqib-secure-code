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


def test_javascript_request_properties_are_structural_sources():
    parsed = parse_source(
        "function route(req) { const id = req.params.id; return id; }",
        "JavaScript",
    )
    result = classify_security_semantics(parsed)

    assert result["sources"][0]["category"] == "http_path_input"
    assert result["sources"][0]["match_type"] == "STRUCTURAL_PATTERN"


def test_filesystem_sinks_and_path_controls_are_observed():
    parsed = parse_source(
        '''
from pathlib import Path
from flask import request

def read_file():
    name = request.args.get("name")
    target = Path("/srv/data", name).resolve()
    return target.read_text()
'''.strip(),
        "Python",
    )
    result = classify_security_semantics(parsed)

    assert {item["target"] for item in result["sinks"]} == {"target.read_text"}
    assert any(item["category"] == "path_normalization" for item in result["security_controls"])


def test_unrelated_reopen_call_is_not_a_filesystem_sink():
    parsed = parse_source("def run():\n    reopen()\n", "Python")
    assert classify_security_semantics(parsed)["sinks"] == []


def test_flask_route_parameter_is_bound_as_path_input():
    parsed = parse_source(
        '''from flask import Flask
app = Flask(__name__)
@app.get("/files/<path:name>")
def download(name):
    return open(name).read()
''',
        "Python",
    )
    result = classify_security_semantics(parsed)
    source = result["sources"][0]
    assert source["category"] == "http_path_input"
    assert source["binding"] == "name"


def test_authorization_sensitive_object_access_is_only_a_sink_observation():
    parsed = parse_source(
        '''from flask import request
def detail():
    object_id = request.args.get("id")
    return Document.query.get(object_id)
''',
        "Python",
    )
    result = classify_security_semantics(parsed)
    assert result["sinks"][0]["category"] == (
        "authorization_sensitive_object_access"
    )
