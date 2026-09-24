from app.analysis_service import analyze_source_file


def test_candidate_pipeline_blocks_patch_and_download_without_verification():
    result = analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\ndef run():\n    os.system(request.args.get("command"))\n''',
    )
    pipeline = result["pipeline"]
    stages = {item["name"]: item for item in pipeline["stages"]}

    assert pipeline["current_stage"] == "EXPLOITABILITY_VERIFICATION"
    assert stages["EXPLOITABILITY_VERIFICATION"]["status"] == "BLOCKED"
    assert stages["MINIMAL_SECURE_PATCH"] == {
        "name": "MINIMAL_SECURE_PATCH",
        "status": "BLOCKED",
        "blockers": ["EXPLOITABILITY_NOT_VERIFIED"],
    }
    assert pipeline["updated_artifact"] == {
        "status": "NOT_AVAILABLE",
        "reason": "NO_VERIFIED_PATCH",
        "original_overwritten": False,
    }
    assert pipeline["claims"]["finding_closed"] is False


def test_no_candidate_does_not_claim_closure_or_create_artifact():
    result = analyze_source_file("safe.py", b"def add(a, b):\n    return a + b\n")
    pipeline = result["pipeline"]
    stages = {item["name"]: item for item in pipeline["stages"]}

    assert stages["SECURITY_ANALYSIS"]["status"] == "COMPLETED_NO_CANDIDATE"
    assert stages["MINIMAL_SECURE_PATCH"]["status"] == "NOT_REQUIRED"
    assert pipeline["updated_artifact"]["status"] == "NOT_AVAILABLE"
