from app.analysis_service import analyze_source_file


def _flow(source: str) -> dict:
    return analyze_source_file(
        "example.py",
        source.strip().encode(),
    )["inter_function_data_flow"]


def test_source_crosses_one_verified_local_call_boundary():
    result = _flow(
        '''
from flask import request
import os

def execute(command):
    os.system(command)

def route():
    raw = request.args.get("command")
    execute(raw)
'''
    )

    assert result["counts"]["observed_paths"] == 1
    path = result["paths"][0]
    assert path["scope"] == {
        "caller": "route",
        "callee": "execute",
        "call_depth": 1,
    }
    assert [step["kind"] for step in path["trace"]] == [
        "SOURCE",
        "ASSIGNMENT",
        "CALL_ARGUMENT",
        "CALL_BOUNDARY",
        "PARAMETER",
        "SINK",
    ]


def test_direct_source_call_argument_crosses_boundary():
    result = _flow(
        '''
from flask import request
import os

def execute(command):
    os.system(command)

def route():
    execute(request.args.get("command"))
'''
    )

    assert result["counts"]["observed_paths"] == 1


def test_mutually_exclusive_caller_branches_do_not_cross():
    result = _flow(
        '''
from flask import request
import os

def execute(command):
    os.system(command)

def route(flag):
    if flag:
        raw = request.args.get("command")
    else:
        execute(raw)
'''
    )

    assert result["paths"] == []


def test_unresolved_external_call_is_not_followed():
    result = _flow(
        '''
from flask import request

def route():
    raw = request.args.get("command")
    external.execute(raw)
'''
    )

    assert result["paths"] == []


def test_control_in_callee_remains_unverified():
    result = _flow(
        '''
from flask import request
import os
import shlex

def execute(raw):
    command = shlex.quote(raw)
    os.system(command)

def route():
    raw = request.args.get("command")
    execute(raw)
'''
    )

    path = result["paths"][0]
    assert len(path["controls_observed"]) == 1
    assert path["control_assessment"] == "UNVERIFIED_APPLICABILITY"
    assert path["status"] == "OBSERVED"
