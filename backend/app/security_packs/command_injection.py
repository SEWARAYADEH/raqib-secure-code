"""Conservative static distinction between shell text and process arguments."""

from __future__ import annotations

import ast
from pathlib import PurePath


NON_SHELL_ARGUMENT_FLOW = "NON_SHELL_ARGUMENT_FLOW"
UNRESOLVED = "COMMAND_EXECUTION_CONTEXT_UNRESOLVED"
_SHELL_EXECUTABLES = {
    "sh", "bash", "dash", "zsh", "fish", "cmd", "cmd.exe",
    "powershell", "powershell.exe", "pwsh", "pwsh.exe",
}


def assess_command_path(path: dict, parsed: dict) -> dict:
    """Suppress only an observed argument flow with explicit shell=False.

    This does not prove the called program interprets its arguments safely.
    Unknown call shapes remain candidates for human review.
    """
    sink = path["sink"]
    if parsed.get("language") != "Python" or sink["category"] != "process_execution":
        return _result(UNRESOLVED, "OUTSIDE_SUPPORTED_CALL_SHAPE")
    calls = [
        call for call in parsed.get("calls", [])
        if call.get("target") == sink["target"]
        and call.get("start_line") == sink["start_line"]
        and call.get("start_column") == sink["start_column"]
    ]
    if len(calls) != 1:
        return _result(UNRESOLVED, "SINK_CALL_NOT_UNIQUE")
    try:
        expression = ast.parse(
            "f" + calls[0]["arguments"], mode="eval"
        ).body
    except (SyntaxError, TypeError, ValueError, MemoryError, RecursionError):
        return _result(UNRESOLVED, "ARGUMENTS_NOT_PARSEABLE")
    if not isinstance(expression, ast.Call) or not expression.args:
        return _result(UNRESOLVED, "COMMAND_ARGUMENT_NOT_OBSERVED")
    keywords = {item.arg: item.value for item in expression.keywords if item.arg}
    if "executable" in keywords or any(item.arg is None for item in expression.keywords):
        return _result(UNRESOLVED, "EXECUTABLE_OVERRIDE_OR_DYNAMIC_KEYWORDS")
    shell = keywords.get("shell")
    if not isinstance(shell, ast.Constant) or shell.value is not False:
        return _result(UNRESOLVED, "SHELL_NOT_EXPLICITLY_FALSE")
    command = expression.args[0]
    if not isinstance(command, (ast.List, ast.Tuple)) or not command.elts:
        return _result(UNRESOLVED, "COMMAND_NOT_ARGUMENT_LIST")
    executable = command.elts[0]
    if not isinstance(executable, ast.Constant) or not isinstance(executable.value, str):
        return _result(UNRESOLVED, "EXECUTABLE_NOT_FIXED_LITERAL")
    name = PurePath(executable.value.replace("\\", "/")).name.casefold()
    if not name or name in _SHELL_EXECUTABLES:
        return _result(UNRESOLVED, "SHELL_OR_EMPTY_EXECUTABLE")
    return _result(NON_SHELL_ARGUMENT_FLOW, "FIXED_EXECUTABLE_LIST_AND_SHELL_FALSE")


def _result(status: str, basis: str) -> dict:
    return {
        "pack": "COMMAND_INJECTION",
        "status": status,
        "basis": basis,
        "scope": "PYTHON_SUBPROCESS_ARGUMENT_SHAPE_ONLY",
        "argument_semantics": "UNRESOLVED",
        "runtime_effectiveness_verified": False,
    }
