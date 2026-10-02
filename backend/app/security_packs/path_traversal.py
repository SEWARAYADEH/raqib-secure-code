"""Conservative static assessment for user-controlled filesystem paths."""

from __future__ import annotations


PATH_INFLUENCE_CANDIDATE = "PATH_INFLUENCE_CANDIDATE"
PATH_CONTROL_OBSERVED = "PATH_CONTROL_OBSERVED_UNVERIFIED"


def assess_path_path(path: dict, _parsed: dict) -> dict:
    controls = {
        item.get("category") for item in path.get("controls_observed", [])
    }
    required = {"path_normalization", "path_containment_check"}
    if required.issubset(controls):
        return _result(PATH_CONTROL_OBSERVED, "NORMALIZATION_AND_CONTAINMENT_OBSERVED")
    if "filename_sanitization" in controls:
        return _result(PATH_CONTROL_OBSERVED, "FILENAME_SANITIZATION_OBSERVED")
    return _result(PATH_INFLUENCE_CANDIDATE, "INPUT_REACHES_FILESYSTEM_PATH_ARGUMENT")


def _result(status: str, basis: str) -> dict:
    return {
        "pack": "PATH_TRAVERSAL",
        "status": status,
        "basis": basis,
        "scope": "OBSERVED_SOURCE_TO_FILESYSTEM_CALL",
        "allowed_root": "UNRESOLVED",
        "runtime_effectiveness_verified": False,
    }
