"""Narrow, static repair proposals for observed Python call shapes.

This module never executes uploaded source or claims functional verification.
Unsupported shapes fail closed instead of receiving a guessed edit.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import re
import shlex
from datetime import datetime, timezone

from app.analysis_service import analyze_source_file
from app.closure_evaluator import evaluate_closure
from app.intake import inspect_source_file
from app.trusted_sql_functional import test_trusted_sql_normal_input


class RepairNotAvailable(ValueError):
    pass


def propose_repair(filename: str, content: bytes, finding_id: str) -> dict:
    intake = inspect_source_file(filename, content)
    if intake["encoding"] != "UTF-8":
        raise RepairNotAvailable("This proposal requires a UTF-8 file without BOM.")
    original = analyze_source_file(filename, content)
    finding = next((item for item in original["security_analysis"]["candidates"]
                    if item["id"] == finding_id), None)
    if finding is None or original["language"]["candidate"] != "Python":
        raise RepairNotAvailable("The saved Python finding was not reproduced.")
    source = intake["source_text"]
    try:
        tree = ast.parse(source, filename=filename)
    except (SyntaxError, ValueError, MemoryError, RecursionError) as exc:
        raise RepairNotAvailable("Python syntax is not suitable for an automatic proposal.") from exc
    function = next((node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and node.name == finding["scope"]["function"]
                     and node.lineno == finding["scope"]["start_line"]), None)
    if function is None:
        raise RepairNotAvailable("The finding function cannot be uniquely located.")
    category = finding["sink"]["category"]
    if category == "sql_execution_candidate":
        edits = _sqlite_edits(source, function, finding)
    elif category == "process_execution":
        edits = _subprocess_edits(source, function, finding)
    else:
        raise RepairNotAvailable("No reviewed repair template covers this sink.")
    updated = _apply_line_edits(source, edits)
    updated_result = analyze_source_file(filename, updated.encode("utf-8"))
    remaining = [item for item in updated_result["security_analysis"]["candidates"]
                 if item["scope"]["function"] == finding["scope"]["function"]
                 and item["sink"]["category"] == category]
    after_paths = [item for item in updated_result["security_analysis"]["non_candidates"]
                   if item["sink"]["category"] == category
                   and item["sink"]["target"] == finding["sink"]["target"]
                   and item["sink"]["start_line"] == finding["sink"]["start_line"]]
    static_retrace = {
        "status": "OBSERVED_NON_CANDIDATE" if after_paths else "UNRESOLVED",
        "before_trace": finding["trace"],
        "after_paths": [
            {"trace": item["trace"], "assessment": item["assessment"]}
            for item in after_paths
        ],
        "interpretation": "STATIC_ONLY_NOT_RUNTIME_PROOF",
    }
    diff = "".join(difflib.unified_diff(
        source.splitlines(keepends=True), updated.splitlines(keepends=True),
        fromfile=filename, tofile=f"{filename}.proposed",
    ))
    root_cause = {
        "status": "STATICALLY_SUPPORTED" if category == "sql_execution_candidate" else "CANDIDATE",
        "category": "SQL_TEXT_CONCATENATION" if category == "sql_execution_candidate" else "SHELL_COMMAND_CONSTRUCTION",
        "finding_id": finding_id,
        "source_location": {"file": filename, "line": finding["source"]["start_line"]},
        "sink_location": {"file": filename, "line": finding["sink"]["start_line"]},
        "evidence": finding["trace"],
        "explanation": "Observed input is concatenated into SQL text before execution; the reviewed patch binds it as a parameter." if category == "sql_execution_candidate" else "Observed input enters a shell command string.",
        "runtime_confirmed": False,
    }
    proposal = {
        "status": "PROPOSED_UNVERIFIED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "analyzer_version": original["analyzer_version"],
        "original_sha256": intake["sha256"],
        "updated_sha256": hashlib.sha256(updated.encode("utf-8")).hexdigest(),
        "finding_id": finding_id,
        "filename": filename,
        "diff": diff,
        "updated_source": updated,
        "static_reanalysis": {
            "syntax_valid": updated_result["structure"]["syntax"]["valid"],
            "same_function_category_candidates": len(remaining),
            "status": "NO_MATCH_OBSERVED" if not remaining else "CANDIDATE_REMAINS",
        },
        "static_retrace": static_retrace,
        "root_cause": root_cause,
        "functional_test": "NOT_RUN",
        "functional_evidence": {"status": "NOT_AVAILABLE", "reason": "NO_TRUSTED_FUNCTIONAL_SCENARIO"},
        "runtime_replay": "NOT_RUN",
        "verified_closed": False,
    }
    if category == "sql_execution_candidate":
        functional = test_trusted_sql_normal_input(intake["sha256"], proposal)
        proposal["functional_evidence"] = functional
        proposal["functional_test"] = functional["status"] if functional["status"] != "NOT_AVAILABLE" else "NOT_RUN"
    proposal["closure_evaluation"] = evaluate_closure(
        finding=finding, proposal=proposal, functional=proposal["functional_evidence"],
    )
    proposal["verified_closed"] = proposal["closure_evaluation"]["verified_closed"]
    return proposal


def _sqlite_edits(source: str, function: ast.AST, finding: dict) -> dict[int, str]:
    if not any(isinstance(node, ast.Call) and _call_name(node) == "sqlite3.connect"
               for node in ast.walk(function)):
        raise RepairNotAvailable("SQLite connection evidence is missing.")
    sink = _sink_call(function, finding)
    if len(sink.args) != 1 or sink.keywords or not isinstance(sink.args[0], ast.Name):
        raise RepairNotAvailable("SQL execute shape is not supported.")
    query_name = sink.args[0].id
    assignments = [node for node in ast.walk(function)
                   if isinstance(node, ast.Assign) and len(node.targets) == 1
                   and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == query_name]
    if len(assignments) != 1:
        raise RepairNotAvailable("Query assignment is not unique.")
    assignment = assignments[0]
    value = assignment.value
    if not (isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add)
            and isinstance(value.left, ast.Constant) and isinstance(value.left.value, str)
            and value.left.value.rstrip().upper().endswith(" ID =")
            and isinstance(value.right, ast.Call) and _call_name(value.right) == "str"
            and len(value.right.args) == 1 and isinstance(value.right.args[0], ast.Name)):
        raise RepairNotAvailable("Only a literal SQLite ID query plus str(input) is supported.")
    parameter = value.right.args[0].id
    if not any(step.get("kind") == "ASSIGNMENT" and step.get("target") == parameter
               for step in finding["trace"]):
        raise RepairNotAvailable("The query parameter is not on the observed trace.")
    lines = source.splitlines()
    before_assignment = lines[assignment.lineno - 1]
    before_sink = lines[sink.lineno - 1]
    if assignment.lineno != assignment.end_lineno or sink.lineno != sink.end_lineno:
        raise RepairNotAvailable("Multi-line SQL edits require manual review.")
    expected_call = ast.get_source_segment(source, sink)
    if expected_call != f"{finding['sink']['target']}({query_name})":
        raise RepairNotAvailable("SQL sink text changed from the supported shape.")
    indentation = re.match(r"\s*", before_assignment).group()
    return {
        assignment.lineno: f"{indentation}{query_name} = {value.left.value + '?'!r}",
        sink.lineno: before_sink.replace(
            expected_call,
            f"{finding['sink']['target']}({query_name}, ({parameter},))", 1,
        ),
    }


def _subprocess_edits(source: str, function: ast.AST, finding: dict) -> dict[int, str]:
    sink = _sink_call(function, finding)
    if _call_name(sink) not in {"subprocess.run", "subprocess.call", "subprocess.check_call"}:
        raise RepairNotAvailable("This subprocess API has no reviewed repair template.")
    if len(sink.args) != 1 or not isinstance(sink.args[0], ast.Name):
        raise RepairNotAvailable("A single named command argument is required.")
    shell_keywords = [item for item in sink.keywords if item.arg == "shell"]
    if len(shell_keywords) != 1 or not isinstance(shell_keywords[0].value, ast.Constant) or shell_keywords[0].value.value is not True:
        raise RepairNotAvailable("Only explicit shell=True is supported.")
    if any(item.arg is None or item.arg == "executable" for item in sink.keywords):
        raise RepairNotAvailable("Dynamic keywords or executable overrides are unsupported.")
    command_name = sink.args[0].id
    assignments = [node for node in ast.walk(function)
                   if isinstance(node, ast.Assign) and len(node.targets) == 1
                   and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == command_name]
    if len(assignments) != 1:
        raise RepairNotAvailable("Command assignment is not unique.")
    value = assignments[0].value
    if not (isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add)
            and isinstance(value.left, ast.Constant) and isinstance(value.left.value, str)
            and value.left.value.endswith(" ")
            and isinstance(value.right, ast.Call) and _call_name(value.right) == "str"
            and len(value.right.args) == 1 and isinstance(value.right.args[0], ast.Name)):
        raise RepairNotAvailable("Only a literal command prefix plus str(input) is supported.")
    parameter = value.right.args[0].id
    if not any(step.get("kind") == "ASSIGNMENT" and step.get("target") == parameter
               for step in finding["trace"]):
        raise RepairNotAvailable("The command parameter is not on the observed trace.")
    try:
        prefix = shlex.split(value.left.value)
    except ValueError as exc:
        raise RepairNotAvailable("Command prefix cannot be tokenized safely.") from exc
    if (len(prefix) < 1
            or prefix[0].casefold() in {"sh", "bash", "cmd", "cmd.exe", "powershell", "pwsh"}
            or any(token in {";", "|", "||", "&&", ">", "<", "$()"} for token in prefix)):
        raise RepairNotAvailable("Shell interpreters require manual review.")
    lines = source.splitlines()
    argument = sink.args[0]
    shell = shell_keywords[0].value
    if argument.lineno == shell.lineno or argument.lineno == assignments[0].lineno:
        raise RepairNotAvailable("Compact command calls require manual review.")
    argument_line = lines[argument.lineno - 1]
    shell_line = lines[shell.lineno - 1]
    if argument_line.strip() != f"{command_name}," or shell_line.strip() != "shell=True,":
        raise RepairNotAvailable("Command call formatting is not supported.")
    rendered = "[" + ", ".join([*(repr(token) for token in prefix), f"str({parameter})"]) + "]"
    return {
        argument.lineno: argument_line.replace(command_name, rendered, 1),
        shell.lineno: shell_line.replace("shell=True", "shell=False", 1),
    }


def _sink_call(function: ast.AST, finding: dict) -> ast.Call:
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)
             and node.lineno == finding["sink"]["start_line"]
             and _call_name(node) == finding["sink"]["target"]]
    if len(calls) != 1:
        raise RepairNotAvailable("The sensitive call is not unique.")
    return calls[0]


def _call_name(node: ast.Call) -> str:
    try:
        return ast.unparse(node.func)
    except (ValueError, RecursionError):
        return ""


def _apply_line_edits(source: str, edits: dict[int, str]) -> str:
    lines = source.splitlines(keepends=True)
    for number, replacement in edits.items():
        ending = "\r\n" if lines[number - 1].endswith("\r\n") else "\n" if lines[number - 1].endswith("\n") else ""
        lines[number - 1] = replacement + ending
    return "".join(lines)
