from __future__ import annotations

from app.application_model import build_application_model
from app.application_context import enrich_application_understanding
from app.control_flow import build_control_flow_model
from app.codex_advisor import AdvisorConfig, advisor_status
from app.data_flow import build_intra_function_data_flow
from app.framework_intelligence import understand_frameworks
from app.finding_model import build_finding_candidates
from app.intake import inspect_source_file
from app.language_detection import detect_language
from app.interprocedural_flow import (
    build_inter_function_data_flow,
)
from app.javascript_bindings import javascript_binding_evidence
from app.parser_engine import (
    LANGUAGE_CONFIG,
    parse_source,
)
from app.pipeline_state import build_pipeline_state
from app.project_calls import python_binding_evidence
from app.relationship_model import build_relationship_model
from app.security_semantics import (
    classify_security_semantics,
)
from app.verification_planner import build_verification_plans
from flask import current_app, has_app_context


ANALYSIS_SCHEMA_VERSION = "1.0"


class AnalysisValidationError(ValueError):
    pass


def analyze_source_file(
    filename: str,
    content: bytes,
) -> dict:
    intake = inspect_source_file(filename, content)
    language = detect_language(
        intake["language_hint"],
        intake["source_text"],
    )
    candidate = language["candidate"]

    if candidate is None:
        raise AnalysisValidationError(
            "The source language could not be established "
            "from consistent evidence."
        )

    if candidate not in LANGUAGE_CONFIG:
        raise AnalysisValidationError(
            f"No verified parser is available for {candidate}."
        )

    parsed = parse_source(
        intake["source_text"],
        candidate,
    )
    relationships = build_relationship_model(parsed)
    understanding = understand_frameworks(parsed)
    semantics = classify_security_semantics(parsed)
    understanding = enrich_application_understanding(
        parsed=parsed,
        semantics=semantics,
        base=understanding,
    )
    control_flow = build_control_flow_model(parsed)
    data_flow = build_intra_function_data_flow(
        parsed,
        semantics,
        control_flow,
    )
    inter_function_data_flow = build_inter_function_data_flow(
        parsed=parsed,
        relationships=relationships,
        semantics=semantics,
        control_flow=control_flow,
    )
    artifact = {
        key: value
        for key, value in intake.items()
        if key != "source_text"
    }
    application_model = build_application_model(
        artifact=artifact,
        parsed=parsed,
        relationships=relationships,
        semantics=semantics,
        data_flow=data_flow,
        control_flow=control_flow,
        understanding=understanding,
    )
    findings = build_finding_candidates(
        artifact=artifact,
        intra_function_flow=data_flow,
        inter_function_flow=inter_function_data_flow,
    )
    verification = build_verification_plans(
        findings,
        isolation_runtime_available=(
            bool(current_app.config["ISOLATION_RUNTIME_AVAILABLE"])
            if has_app_context()
            else False
        ),
    )
    pipeline = build_pipeline_state(
        findings=findings,
        verification=verification,
    )
    advisor = _advisor_status()

    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "analysis": {
            "scope": "FILE",
            "execution_policy": "NEVER_EXECUTE_SOURCE",
            "finding_policy": "EVIDENCE_GATED_CANDIDATES",
        },
        "artifact": artifact,
        "language": language,
        "structure": parsed,
        "python_binding_evidence": (
            python_binding_evidence(intake["source_text"])
            if candidate == "Python"
            else None
        ),
        "javascript_binding_evidence": (
            javascript_binding_evidence(intake["source_text"])
            if candidate in {"JavaScript", "JavaScript JSX"}
            else None
        ),
        "relationships": relationships,
        "application_understanding": understanding,
        "security_semantics": semantics,
        "control_flow": control_flow,
        "data_flow": data_flow,
        "inter_function_data_flow": inter_function_data_flow,
        "application_model": application_model,
        "security_analysis": findings,
        "exploitability_verification": verification,
        "pipeline": pipeline,
        "codex_advisor": advisor,
    }


def _advisor_status() -> dict:
    if not has_app_context():
        return advisor_status(AdvisorConfig(False, "", ""))
    return advisor_status(
        AdvisorConfig(
            enabled=bool(current_app.config["CODEX_ADVISOR_ENABLED"]),
            api_key=current_app.config["OPENAI_API_KEY"],
            model=current_app.config["OPENAI_MODEL"],
            max_context_characters=current_app.config[
                "CODEX_CONTEXT_MAX_CHARACTERS"
            ],
        )
    )
