import io
import zipfile

from app.analysis_service import analyze_source_file
from app.archive_service import analyze_source_archive


def test_code_correlation_preserves_candidate_and_standard_boundary():
    result = analyze_source_file(
        "route.py",
        b'from flask import request\nimport os\n'
        b'def run():\n    os.system(request.args.get("command"))\n',
    )
    hybrid = result["hybrid_security"]
    correlation = hybrid["correlations"][0]

    assert correlation["candidate_id"] == (
        result["security_analysis"]["candidates"][0]["id"]
    )
    assert correlation["source_rule_id"] == "PY-SRC-FLASK-QUERY"
    assert correlation["sink_rule_id"] == "PY-SINK-OS-SYSTEM"
    assert correlation["standards"]["cwe"] == "CWE-78"
    assert correlation["standards"]["status"] == "CANDIDATE_MAPPING"
    assert correlation["exploitability"] == "UNVERIFIED"
    assert hybrid["sensors"]["external_sast"] == "NOT_RUN"


def test_project_keeps_code_and_dependency_evidence_independent(tmp_path):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "route.py",
            'from flask import request\nimport os\n'
            'def run():\n    os.system(request.args.get("command"))\n',
        )
        archive.writestr("requirements.txt", "Flask==3.1.3\n")
    result = analyze_source_archive(
        filename="project.zip", content=output.getvalue(),
        workspace_root=str(tmp_path),
    )
    project = result["project_understanding"]
    hybrid = project["hybrid_security"]

    assert hybrid["counts"]["code_candidates"] == 1
    assert hybrid["counts"]["dependency_advisory_matches"] == 0
    assert hybrid["counts"]["verified_vulnerabilities"] == 0
    assert hybrid["sensors"]["dependency_advisories"] == "DISABLED"
    assert hybrid["code_correlations"][0]["file"] == "route.py"
