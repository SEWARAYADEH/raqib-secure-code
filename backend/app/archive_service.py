from __future__ import annotations

from pathlib import Path

from flask import current_app, has_app_context

from app.analysis_service import AnalysisValidationError, analyze_source_file
from app.archive_intake import (
    SourceArchiveValidationError,
    extract_source_archive,
)
from app.intake import SourceFileValidationError
from app.dependency_advisories import check_dependency_advisories
from app.hybrid_security import correlate_project_evidence
from app.security_packs.registry import pack_coverage
from app.project_understanding import build_project_understanding
from app.finding_model import build_project_finding_candidates
from app.workspace import AnalysisWorkspace


def analyze_source_archive(
    *,
    filename: str,
    content: bytes,
    workspace_root: str,
) -> dict:
    with AnalysisWorkspace(workspace_root) as workspace:
        archive = extract_source_archive(
            filename=filename,
            content=content,
            workspace=workspace,
        )
        file_results = []

        for file_record in archive["files"]:
            source = Path(
                file_record["workspace_path"]
            ).read_bytes()
            try:
                result = analyze_source_file(
                    Path(file_record["relative_path"]).name,
                    source,
                )
            except (SourceFileValidationError, AnalysisValidationError) as exc:
                raise SourceArchiveValidationError(
                    f"Invalid source member: {file_record['relative_path']}. "
                    f"{exc}"
                ) from exc
            result["artifact"]["relative_path"] = file_record[
                "relative_path"
            ]
            file_results.append(result)

    project_understanding = build_project_understanding(
        file_results, archive["manifests"]
    )
    project_understanding["dependency_advisories"] = (
        check_dependency_advisories(
            project_understanding["dependency_declarations"],
            enabled=bool(current_app.config["OSV_ADVISORY_LOOKUP_ENABLED"])
            if has_app_context() else False,
        )
    )
    project_understanding["hybrid_security"] = correlate_project_evidence(
        file_results, project_understanding["dependency_advisories"]
    )
    project_findings = build_project_finding_candidates(
        artifact={
            key: value for key, value in archive.items()
            if key not in {"files", "manifests", "skipped_files"}
        },
        paths=project_understanding["cross_file_data_flow"],
        file_results=file_results,
    )

    return {
        "schema_version": "1.0",
        "analysis": {
            "scope": "PROJECT_STATIC_MODEL",
            "execution_policy": "NEVER_EXECUTE_SOURCE",
            "finding_policy": "EVIDENCE_GATED_CANDIDATES",
            "cross_file_tracing": (
                "PARTIAL_STATIC"
                if project_understanding["cross_file_data_flow"]
                else "UNRESOLVED"
            ),
        },
        "artifact": {
            key: value
            for key, value in archive.items()
            if key not in {"files", "manifests"}
        },
        "files": file_results,
        "project_understanding": project_understanding,
        "security_analysis": project_findings,
        "security_packs": pack_coverage(),
        "counts": {
            "analyzed_files": len(file_results),
            "intra_function_paths": sum(
                item["data_flow"]["counts"][
                    "observed_paths"
                ]
                for item in file_results
            ),
            "inter_function_paths": sum(
                item["inter_function_data_flow"]["counts"][
                    "observed_paths"
                ]
                for item in file_results
            ),
            "cross_file_paths": len(project_understanding["cross_file_data_flow"]),
            "cross_file_candidates": project_findings["counts"]["candidates"],
        },
    }
