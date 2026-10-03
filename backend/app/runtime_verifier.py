"""Fail-closed OCI execution for narrowly reviewed finding replay scenarios.

Uploaded Python is executed only inside a pre-installed, digest-pinned OCI image.
The container has no network, no capabilities, a read-only root filesystem, a
non-root identity, strict resource limits, and a read-only input mount.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


_IMAGE_DIGEST = re.compile(r"^[a-z0-9./_-]+(?:\:[a-z0-9._-]+)?@sha256:[0-9a-f]{64}$")
_SUPPORTED_CATEGORIES = {"sql_execution_candidate", "process_execution"}


class RuntimeVerifier(Protocol):
    def capability(self) -> dict: ...
    def verify_repair(
        self, *, filename: str, original: bytes, patched: bytes, finding: dict
    ) -> dict: ...


class UnavailableRuntimeVerifier:
    def __init__(self, reason: str = "NO_REVIEWED_ISOLATED_EXECUTOR") -> None:
        self.reason = reason

    def capability(self) -> dict:
        return {"available": False, "status": "NOT_AVAILABLE", "reason": self.reason}

    def verify_repair(
        self, *, filename: str, original: bytes, patched: bytes, finding: dict
    ) -> dict:
        del filename, original, patched, finding
        raise RuntimeError("Runtime isolation is not available.")


@dataclass(frozen=True)
class OciRuntimeConfig:
    engine: str
    image: str
    timeout_seconds: int = 15
    memory_megabytes: int = 256
    cpu_limit: str = "0.5"
    process_limit: int = 32


class OciRuntimeVerifier:
    """Execute the trusted replay harness with untrusted source as read-only input."""

    def __init__(self, config: OciRuntimeConfig) -> None:
        self.config = config

    def capability(self) -> dict:
        if self.config.engine not in {"docker", "podman"}:
            return _unavailable("UNSUPPORTED_OCI_ENGINE")
        executable = _resolve_engine_executable(self.config.engine)
        if executable is None:
            return _unavailable("OCI_ENGINE_NOT_INSTALLED")
        if not _IMAGE_DIGEST.fullmatch(self.config.image):
            return _unavailable("RUNTIME_IMAGE_NOT_DIGEST_PINNED")
        try:
            inspected = subprocess.run(
                [executable, "image", "inspect", self.config.image, "--format", "{{.Id}}"],
                capture_output=True, check=False, text=True, timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return _unavailable("OCI_ENGINE_UNREACHABLE")
        if inspected.returncode != 0 or not inspected.stdout.strip().startswith("sha256:"):
            return _unavailable("PINNED_RUNTIME_IMAGE_UNAVAILABLE")
        return {
            "available": True,
            "status": "AVAILABLE",
            "engine": self.config.engine,
            "image": self.config.image,
            "image_id": inspected.stdout.strip(),
            "policy": _policy(self.config),
        }

    def verify_repair(
        self, *, filename: str, original: bytes, patched: bytes, finding: dict
    ) -> dict:
        capability = self.capability()
        if not capability["available"]:
            raise RuntimeError(capability["reason"])
        category = finding.get("sink", {}).get("category")
        if category not in _SUPPORTED_CATEGORIES:
            raise ValueError("No reviewed isolated replay supports this finding category.")
        if Path(filename).suffix.casefold() != ".py":
            raise ValueError("The reviewed runtime verifier supports Python files only.")
        if not original or not patched or len(original) > 256 * 1024 or len(patched) > 256 * 1024:
            raise ValueError("Runtime verification input is empty or exceeds 256 KB.")

        scenario = {
            "category": category,
            "function": finding.get("scope", {}).get("function"),
            "source_sha256": hashlib.sha256(original).hexdigest(),
            "patched_sha256": hashlib.sha256(patched).hexdigest(),
        }
        if not scenario["function"]:
            raise ValueError("A uniquely resolved function is required for replay.")

        with tempfile.TemporaryDirectory(prefix="raqib-verify-") as temporary:
            root = Path(temporary).resolve()
            (root / "original.py").write_bytes(original)
            (root / "patched.py").write_bytes(patched)
            (root / "scenario.json").write_text(
                json.dumps(scenario, sort_keys=True), encoding="utf-8"
            )
            (root / "runner.py").write_text(_HARNESS, encoding="utf-8")
            try:
                executable = _resolve_engine_executable(self.config.engine)
                if executable is None:
                    return _execution_failure("OCI_ENGINE_NOT_INSTALLED", capability)
                process = subprocess.run(
                    self._command(executable, root),
                    capture_output=True, check=False, text=True,
                    timeout=self.config.timeout_seconds + 2,
                )
            except subprocess.TimeoutExpired as exc:
                return _execution_failure("RUNTIME_TIMEOUT", capability, exc.stdout, exc.stderr)
            except OSError:
                return _execution_failure("OCI_ENGINE_EXECUTION_FAILED", capability)

        if process.returncode != 0:
            return _execution_failure(
                "ISOLATED_HARNESS_FAILED", capability, process.stdout, process.stderr
            )
        try:
            output = json.loads(process.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return _execution_failure(
                "INVALID_HARNESS_EVIDENCE", capability, process.stdout, process.stderr
            )
        if output.get("schema") != "RAQIB_RUNTIME_EVIDENCE_V1":
            return _execution_failure("INVALID_HARNESS_SCHEMA", capability)
        output.update({
            "executor": {
                "engine": capability["engine"], "image": capability["image"],
                "image_id": capability["image_id"], "policy": capability["policy"],
            },
            "source_sha256": scenario["source_sha256"],
            "patched_sha256": scenario["patched_sha256"],
        })
        return output

    def _command(self, executable: str, root: Path) -> list[str]:
        return [
            executable, "run", "--rm", "--network", "none", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", str(self.config.process_limit), "--memory",
            f"{self.config.memory_megabytes}m", "--cpus", self.config.cpu_limit,
            "--user", "65534:65534", "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=16m", "--mount",
            f"type=bind,src={root},dst=/workspace,readonly", "--workdir", "/workspace",
            "--entrypoint", "python", self.config.image, "-I", "-B",
            "/workspace/runner.py",
        ]


def _unavailable(reason: str) -> dict:
    return {"available": False, "status": "NOT_AVAILABLE", "reason": reason}


def _resolve_engine_executable(engine: str) -> str | None:
    executable = shutil.which(engine)
    if executable:
        return executable
    if os.name == "nt" and engine == "docker":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        installed = Path(program_files) / "Docker" / "Docker" / "resources" / "bin" / "docker.exe"
        if installed.is_file():
            return str(installed)
    return None


def _policy(config: OciRuntimeConfig) -> dict:
    return {
        "network": "DENY", "host_filesystem": "READ_ONLY_INPUT_ONLY",
        "host_processes": "DENY", "secrets": "DENY", "identity": "NON_ROOT_65534",
        "root_filesystem": "READ_ONLY", "capabilities": "NONE",
        "no_new_privileges": True, "scratch": "EPHEMERAL_TMPFS_16MB",
        "limits": {"wall_time_seconds": config.timeout_seconds,
                   "memory_megabytes": config.memory_megabytes,
                   "processes": config.process_limit, "cpus": config.cpu_limit},
    }


def _execution_failure(
    reason: str, capability: dict, stdout: str | bytes | None = None,
    stderr: str | bytes | None = None,
) -> dict:
    def digest(value: str | bytes | None) -> str | None:
        if value is None:
            return None
        raw = value if isinstance(value, bytes) else value.encode("utf-8", errors="replace")
        return hashlib.sha256(raw[:64 * 1024]).hexdigest()
    return {
        "schema": "RAQIB_RUNTIME_EVIDENCE_V1", "status": "ERROR", "reason": reason,
        "runtime_before": {"status": "ERROR"},
        "functional_test": {"status": "ERROR"}, "replay_after": {"status": "ERROR"},
        "output_digests": {"stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr)},
        "executor": {key: capability.get(key)
                     for key in ("engine", "image", "image_id", "policy")},
    }


_HARNESS = r'''import importlib.util
import inspect
import json
import pathlib
import sys
import types

MARKER = "RAQIB_MARKER_' OR 1=1 --"
BENIGN = "raqib-safe-value"

class InputMap(dict):
    def get(self, key, default=None, **kwargs): return self.get_value

class Request:
    def __init__(self, value):
        self.args = InputMap(); self.form = InputMap(); self.values = InputMap()
        self.headers = InputMap(); self.cookies = InputMap(); self.json = InputMap()
        for item in (self.args, self.form, self.values, self.headers, self.cookies, self.json):
            item.get_value = value
        self._value = value
    def get_json(self, *args, **kwargs): return self.json
    def get_data(self, *args, **kwargs): return self._value

class Cursor:
    def __init__(self, events): self.events = events
    def execute(self, query, parameters=None):
        self.events.append({"kind": "sql", "query": str(query), "parameters": repr(parameters)})
        return self
    def executemany(self, query, parameters=None): return self.execute(query, parameters)
    def fetchall(self): return []
    def fetchone(self): return None

class Connection:
    def __init__(self, events): self.events = events
    def cursor(self): return Cursor(self.events)
    def execute(self, query, parameters=None): return Cursor(self.events).execute(query, parameters)
    def commit(self): return None
    def close(self): return None

class DummyApp:
    def route(self, *args, **kwargs): return lambda function: function
    def get(self, *args, **kwargs): return lambda function: function
    def post(self, *args, **kwargs): return lambda function: function

def run(path, function_name, value):
    events = []
    flask = types.ModuleType("flask"); flask.request = Request(value)
    flask.Flask = lambda *args, **kwargs: DummyApp()
    flask.abort = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("abort"))
    flask.jsonify = lambda value=None, **kwargs: value if value is not None else kwargs
    flask.send_file = lambda *args, **kwargs: None
    sqlite = types.ModuleType("sqlite3"); sqlite.connect = lambda *args, **kwargs: Connection(events)
    sub = types.ModuleType("subprocess")
    def subprocess_call(args, *positional, **kwargs):
        events.append({"kind": "command", "api": "subprocess", "args": repr(args),
                       "shell": kwargs.get("shell", False)})
        return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
    for name in ("run", "call", "check_call", "check_output", "getoutput",
                 "getstatusoutput", "Popen"): setattr(sub, name, subprocess_call)
    originals = {name: sys.modules.get(name) for name in ("flask", "sqlite3", "subprocess")}
    import os
    original_system, original_popen = os.system, os.popen
    os.system = lambda command: events.append({"kind": "command", "api": "os.system",
                                               "args": repr(command), "shell": True}) or 0
    os.popen = lambda command: events.append({"kind": "command", "api": "os.popen",
                                              "args": repr(command), "shell": True}) or types.SimpleNamespace(read=lambda: "")
    sys.modules.update({"flask": flask, "sqlite3": sqlite, "subprocess": sub})
    try:
        name = "target_" + pathlib.Path(path).stem + "_" + str(abs(hash((path, value))))
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        function = getattr(module, function_name); signature = inspect.signature(function)
        arguments = [value for item in signature.parameters.values()
                     if item.default is inspect.Parameter.empty and item.kind in
                     (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        function(*arguments)
        return {"completed": True, "events": events, "error_type": None}
    except Exception as error:
        return {"completed": False, "events": events, "error_type": type(error).__name__}
    finally:
        os.system, os.popen = original_system, original_popen
        for name, previous in originals.items():
            if previous is None: sys.modules.pop(name, None)
            else: sys.modules[name] = previous

def sql_before(events):
    return any(event["kind"] == "sql" and MARKER in event["query"] for event in events)
def sql_after(events):
    return any(event["kind"] == "sql" and MARKER not in event["query"] and
               MARKER in event["parameters"] for event in events)
def command_before(events):
    return any(event["kind"] == "command" and event["shell"] and
               MARKER in event["args"] for event in events)
def command_after(events):
    return any(event["kind"] == "command" and not event["shell"] and
               event["args"].startswith("[") and MARKER in event["args"] for event in events)

ROOT = pathlib.Path(__file__).resolve().parent
scenario = json.loads((ROOT / "scenario.json").read_text(encoding="utf-8"))
before = run(str(ROOT / "original.py"), scenario["function"], MARKER)
after = run(str(ROOT / "patched.py"), scenario["function"], MARKER)
functional = run(str(ROOT / "patched.py"), scenario["function"], BENIGN)
category = scenario["category"]
before_pass = sql_before(before["events"]) if category == "sql_execution_candidate" else command_before(before["events"])
after_pass = sql_after(after["events"]) if category == "sql_execution_candidate" else command_after(after["events"])
result = {
    "schema": "RAQIB_RUNTIME_EVIDENCE_V1",
    "status": "PASS" if before_pass and after_pass and functional["completed"] else "FAIL",
    "strategy": "CONTROLLED_DEPENDENCY_STUB",
    "runtime_before": {"status": "PASS" if before_pass else "FAIL",
                       "event_count": len(before["events"]), "error_type": before["error_type"]},
    "functional_test": {"status": "PASS" if functional["completed"] else "FAIL",
                        "scope": "TARGET_FUNCTION_SMOKE", "error_type": functional["error_type"]},
    "replay_after": {"status": "PASS" if after_pass else "FAIL",
                     "event_count": len(after["events"]), "error_type": after["error_type"]},
}
print(json.dumps(result, sort_keys=True))
'''
