"""Run checked-in test suites and save bounded results beside the private corpus."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from app.training_store import TrainingStore
from config import Config


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "step-one-secure-code-ai-agent-frontend-professional"
DATABASE = Config.TRAINING_DATABASE_PATH or str(
    BACKEND / "instance" / "training_evaluation.sqlite3"
)


def _run_suite(
    store: TrainingStore, suite: str, command: list[str], cwd: Path,
    junit_path: Path | None = None,
) -> bool:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(BACKEND)
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        process = subprocess.run(
            command, cwd=cwd, env=environment, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=180,
            check=False,
        )
        output = process.stdout + process.stderr
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        output = "Trusted test suite exceeded the 180-second limit."
        exit_code = 124

    if suite == "backend_pytest":
        counts = {
            name: int(match.group(1)) if (match := re.search(rf"(\d+) {name}", output)) else 0
            for name in ("passed", "failed", "skipped")
        }
    elif suite == "frontend_node_tests":
        counts = {
            "passed": _node_count(output, "pass"),
            "failed": _node_count(output, "fail"),
            "skipped": _node_count(output, "skipped"),
        }
    else:
        counts = {"passed": int(exit_code == 0), "failed": int(exit_code != 0), "skipped": 0}
    if exit_code != 0 and counts["failed"] == 0:
        counts["failed"] = 1

    run_id = store.record_test_run(
        suite=suite, command_label=suite, exit_code=exit_code,
        passed_count=counts["passed"], failed_count=counts["failed"],
        skipped_count=counts["skipped"], output=output,
    )
    if suite == "backend_pytest" and junit_path is not None and junit_path.is_file():
        try:
            individual = []
            for case in ET.parse(junit_path).iter("testcase"):
                status = (
                    "FAILED" if case.find("failure") is not None or case.find("error") is not None
                    else "SKIPPED" if case.find("skipped") is not None else "PASSED"
                )
                individual.append((f"{case.attrib['classname']}::{case.attrib['name']}", status))
            store.record_test_results(run_id, individual)
        finally:
            junit_path.unlink(missing_ok=True)
    elif suite == "frontend_node_tests":
        individual = [
            (match.group(2), "PASSED" if match.group(1) == "✔" else "FAILED")
            for match in re.finditer(r"(?m)^\s*([✔✖])\s+(.+?)\s+\([\d.]+ms\)\s*$", output)
        ]
        store.record_test_results(run_id, individual)
    print(
        f"{suite}: {'PASSED' if exit_code == 0 else 'FAILED'} "
        f"passed={counts['passed']} failed={counts['failed']} "
        f"skipped={counts['skipped']} run={run_id}"
    )
    if exit_code != 0:
        print(output[-4000:], file=sys.stderr)
    return exit_code == 0


def _node_count(output: str, name: str) -> int:
    match = re.search(rf"(?m)^\s*[#ℹ]\s*{name}\s+(\d+)\s*$", output)
    return int(match.group(1)) if match else 0


def main() -> int:
    store = TrainingStore(DATABASE)
    cases = store.sync_repository_cases(ROOT / "training", include_large_demo=True)
    npm = shutil.which("npm")
    if npm is None:
        raise RuntimeError("Node.js/npm is required to record frontend test evidence.")

    junit_path = BACKEND / "instance" / f"test-results-{uuid.uuid4().hex}.xml"
    suites = (
        ("backend_pytest", [sys.executable, "-m", "pytest", "backend", "-q",
                            f"--junitxml={junit_path}"], ROOT, junit_path),
        ("frontend_node_tests", [npm, "test"], FRONTEND, None),
        ("frontend_build", [npm, "run", "build"], FRONTEND, None),
    )
    succeeded = [
        _run_suite(store, name, command, working_directory, report)
        for name, command, working_directory, report in suites
    ]
    exported = store.export_jsonl(BACKEND / "instance" / "training_cases.jsonl")
    print(f"training_cases={cases} exported_jsonl={exported} "
          f"recorded_test_results={store.result_counts()['total']}")
    return 0 if all(succeeded) else 1


if __name__ == "__main__":
    raise SystemExit(main())
