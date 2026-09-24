from __future__ import annotations

from pathlib import Path

from app.analysis_service import analyze_source_file
from app.archive_intake import extract_source_archive
from app.project_understanding import build_project_understanding
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
            result = analyze_source_file(
                Path(file_record["relative_path"]).name,
                source,
            )
            result["artifact"]["relative_path"] = file_record[
                "relative_path"
            ]
            file_results.append(result)

    project_understanding = build_project_understanding(file_results)

    return {
        "schema_version": "1.0",
        "analysis": {
            "scope": "PROJECT_STATIC_MODEL",
            "execution_policy": "NEVER_EXECUTE_SOURCE",
            "finding_policy": "EVIDENCE_GATED_CANDIDATES",
            "cross_file_tracing": bool(
                project_understanding["project_data_flow"]["paths"]
            ),
            "cross_file_tracing_scope": (
                project_understanding["project_data_flow"]["scope"]
            ),
        },
        "artifact": {
            key: value
            for key, value in archive.items()
            if key != "files"
        },
        "files": file_results,
        "project_understanding": project_understanding,
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
            "cross_file_paths": project_understanding[
                "project_data_flow"
            ]["counts"]["observed_paths"],
        },
    }
