"""Conservative static assessment for untrusted data reaching HTML/DOM APIs."""

from __future__ import annotations


XSS_OUTPUT_CANDIDATE = "UNENCODED_HTML_OUTPUT_CANDIDATE"
XSS_CONTROL_OBSERVED = "OUTPUT_CONTROL_OBSERVED_UNVERIFIED"


def assess_xss_path(path: dict, _parsed: dict) -> dict:
    controls = {item.get("category") for item in path.get("controls_observed", [])}
    observed = controls & {"output_encoding", "html_sanitization"}
    if observed:
        return _result(XSS_CONTROL_OBSERVED, "OUTPUT_ENCODING_OR_SANITIZATION_OBSERVED")
    return _result(XSS_OUTPUT_CANDIDATE, "INPUT_REACHES_RAW_HTML_OR_DOM_SINK")


def _result(status: str, basis: str) -> dict:
    return {
        "pack": "XSS", "status": status, "basis": basis,
        "scope": "OBSERVED_SOURCE_TO_HTML_DOM_CALL",
        "rendering_context": "UNRESOLVED",
        "runtime_effectiveness_verified": False,
    }
