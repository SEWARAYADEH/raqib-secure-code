import json

import pytest

from app.analysis_service import analyze_source_file
from app.codex_advisor import (
    AdvisorConfig,
    AdvisorUnavailable,
    CodexAdvisor,
    build_minimal_advisor_context,
)


def _analysis():
    return analyze_source_file(
        "route.py",
        b'''from flask import request\nimport os\ndef run():\n    os.system(request.args.get("command"))\n''',
    )


def test_minimal_context_excludes_source_code_and_respects_budget():
    analysis = _analysis()
    finding_id = analysis["security_analysis"]["candidates"][0]["id"]
    context = build_minimal_advisor_context(
        analysis=analysis,
        finding_id=finding_id,
        max_characters=6000,
    )
    serialized = json.dumps(context)

    assert "source_text" not in serialized
    assert "os.system(request" not in serialized
    assert context["budget"]["characters"] <= 6000
    assert context["constraints"]["do_not_claim_verification_or_closure"] is True


def test_disabled_advisor_never_calls_transport():
    advisor = CodexAdvisor(
        AdvisorConfig(False, "", ""),
        transport=lambda _payload: pytest.fail("transport must not run"),
    )
    with pytest.raises(AdvisorUnavailable):
        advisor.advise({"minimal": True})


def test_ready_advisor_uses_strict_schema_and_remains_advisory():
    captured = []
    response = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            {
                                "root_cause_hypotheses": ["hypothesis"],
                                "patch_strategy": "minimal strategy",
                                "test_suggestions": ["test"],
                                "uncertainties": ["runtime not verified"],
                            }
                        ),
                    }
                ]
            }
        ]
    }
    advisor = CodexAdvisor(
        AdvisorConfig(True, "secret", "approved-model"),
        transport=lambda payload: captured.append(payload) or response,
    )
    result = advisor.advise({"minimal": True})

    assert result["authority"] == "ADVISORY_ONLY"
    assert captured[0]["store"] is False
    assert captured[0]["text"]["format"]["strict"] is True
    assert captured[0]["max_output_tokens"] == 1200
