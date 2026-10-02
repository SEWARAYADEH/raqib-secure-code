"""Small fail-closed contract for a future reviewed isolated executor."""

from __future__ import annotations

from typing import Protocol


class RuntimeVerifier(Protocol):
    def capability(self) -> dict: ...
    def prepare(self, analysis_id: str) -> None: ...
    def execute_controlled_test(self, scenario_id: str) -> dict: ...
    def collect_evidence(self) -> dict: ...
    def cleanup(self) -> None: ...


class UnavailableRuntimeVerifier:
    def capability(self) -> dict:
        return {"available": False, "status": "NOT_AVAILABLE",
                "reason": "NO_REVIEWED_ISOLATED_EXECUTOR"}

    def prepare(self, analysis_id: str) -> None:
        raise RuntimeError("Runtime isolation is not available.")

    def execute_controlled_test(self, scenario_id: str) -> dict:
        raise RuntimeError("Runtime isolation is not available.")

    def collect_evidence(self) -> dict:
        raise RuntimeError("Runtime isolation is not available.")

    def cleanup(self) -> None:
        return None
