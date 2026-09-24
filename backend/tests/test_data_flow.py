from app.data_flow import (
    FLOW_KIND,
    FLOW_STATUS,
    build_intra_function_data_flow,
)
from app.parser_engine import parse_source
from app.security_semantics import (
    classify_security_semantics,
)


def _analyze(source: str) -> dict:
    parsed = parse_source(source.strip(), "Python")
    semantics = classify_security_semantics(parsed)
    return build_intra_function_data_flow(
        parsed,
        semantics,
    )


def test_direct_assignment_reaches_command_sink():
    result = _analyze(
        '''
from flask import request
import os

def run():
    command = request.args.get("command")
    os.system(command)
'''
    )

    assert result["counts"]["observed_paths"] == 1
    path = result["paths"][0]
    assert path["kind"] == FLOW_KIND
    assert path["status"] == FLOW_STATUS
    assert path["scope"]["function"] == "run"
    assert path["source"]["target"] == "request.args.get"
    assert path["sink"]["target"] == "os.system"
    assert [step["kind"] for step in path["trace"]] == [
        "SOURCE",
        "ASSIGNMENT",
        "SINK",
    ]


def test_assignment_alias_is_propagated():
    result = _analyze(
        '''
from flask import request
import os

def run():
    raw = request.args.get("command")
    command = raw
    os.system(command)
'''
    )

    trace = result["paths"][0]["trace"]
    assert [
        step.get("target") for step in trace
    ] == [
        "request.args.get",
        "raw",
        "command",
        "os.system",
    ]


def test_data_does_not_cross_function_boundaries():
    result = _analyze(
        '''
from flask import request
import os

def read():
    command = request.args.get("command")
    return command

def run(command):
    os.system(command)
'''
    )

    assert result["paths"] == []


def test_sink_before_source_is_not_a_path():
    result = _analyze(
        '''
from flask import request
import os

def run():
    os.system(command)
    command = request.args.get("command")
'''
    )

    assert result["paths"] == []


def test_direct_nested_source_to_sink_is_observed():
    result = _analyze(
        '''
from flask import request
import os

def run():
    os.system(request.args.get("command"))
'''
    )

    path = result["paths"][0]
    assert [step["kind"] for step in path["trace"]] == [
        "SOURCE",
        "SINK",
    ]


def test_observed_path_is_not_declared_a_vulnerability():
    result = _analyze(
        '''
from flask import request

def load(database):
    user_id = request.args.get("id")
    return database.execute(user_id)
'''
    )

    path = result["paths"][0]
    assert path["evidence_strength"] == "HEURISTIC"
    assert "vulnerability" not in path
    assert "severity" not in path
    assert "cwe" not in path


def test_mutually_exclusive_branches_do_not_form_a_path():
    result = _analyze(
        '''
from flask import request
import os

def run(flag):
    if flag:
        command = request.args.get("command")
    else:
        os.system(command)
'''
    )

    assert result["paths"] == []


def test_branch_path_keeps_explicit_constraint():
    result = _analyze(
        '''
from flask import request
import os

def run(flag):
    if flag:
        command = request.args.get("command")
        os.system(command)
'''
    )

    path = result["paths"][0]
    assert len(path["branch_constraints"]) == 1


def test_tainted_assignment_cannot_cross_to_else_sink():
    result = _analyze(
        '''
from flask import request
import os

def run(flag):
    raw = request.args.get("command")
    if flag:
        command = raw
    else:
        os.system(command)
'''
    )

    assert result["paths"] == []


def test_control_is_recorded_without_declaring_path_safe():
    result = _analyze(
        '''
from flask import request
import os
import shlex

def run():
    raw = request.args.get("command")
    command = shlex.quote(raw)
    os.system(command)
'''
    )

    path = result["paths"][0]
    assert len(path["controls_observed"]) == 1
    assert path["controls_observed"][0]["target"] == "shlex.quote"
    assert path["control_assessment"] == "UNVERIFIED_APPLICABILITY"
    assert path["status"] == "OBSERVED"
