import json
from pathlib import Path

import pytest

from app.analysis_service import analyze_source_file


CASES_PATH = (
    Path(__file__).resolve().parents[2]
    / "training" / "cases" / "sql_injection.json"
)
CASES = json.loads(CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_sql_pack_evaluation_case(case):
    result = analyze_source_file(
        case["language_file"], case["source"].encode("utf-8")
    )
    analysis = result["security_analysis"]
    assert analysis["counts"]["candidates"] == case["expected_candidates"]
    assert analysis["counts"]["non_candidate_paths"] == (
        case["expected_non_candidate_paths"]
    )
    assert analysis["counts"]["verified_vulnerabilities"] == 0
    sql_pack = result["security_packs"][0]
    assert sql_pack["id"] == "SQL_INJECTION"
    assert sql_pack["status"] == "PARTIAL_STATIC_CANDIDATES"
    assert sql_pack["can_verify_exploitability"] is False
    assert sql_pack["can_generate_verified_patch"] is False
    assert sql_pack["can_close"] is False
