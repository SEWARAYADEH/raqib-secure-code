import io

from app import create_app


SOURCE = b"""from flask import request
import os

def run():
    command = request.args.get("command")
    os.system(command)
"""


def _app(tmp_path, **overrides):
    config = {
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "ANALYSIS_STORE_ENABLED": True,
        "ANALYSIS_DATABASE_PATH": str(tmp_path / "analyses.sqlite3"),
        "RECORD_INTEGRITY_KEY": "i" * 40,
        "EMAIL_VERIFICATION_ENABLED": False,
        "CODEX_ADVISOR_ENABLED": True,
        "OPENAI_API_KEY": "server-only-test-key",
        "OPENAI_MODEL": "test-model",
    }
    config.update(overrides)
    return create_app(config)


def _create_analysis(client):
    response = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(SOURCE), "example.py")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    candidates = payload["result"]["security_analysis"]["candidates"]
    assert candidates
    return payload["record"]["analysis_id"], candidates[0]["id"]


def test_advisor_uses_stored_owner_analysis_without_exposing_key(
    tmp_path,
    monkeypatch,
):
    app = _app(tmp_path)
    client = app.test_client()
    analysis_id, finding_id = _create_analysis(client)

    def fake_advise(self, context):
        assert context["finding"]["id"] == finding_id
        return {
            "authority": "ADVISORY_ONLY",
            "model": "test-model",
            "advice": {
                "root_cause_hypotheses": ["Untrusted input reaches a command sink."],
                "patch_strategy": "Avoid shell interpretation and use a constrained API.",
                "test_suggestions": ["Re-run the original functional path."],
                "uncertainties": ["Runtime exploitability has not been verified."],
            },
        }

    monkeypatch.setattr(
        "app.routes.CodexAdvisor.advise",
        fake_advise,
    )
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/advisor",
        json={"finding_id": finding_id},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["result"]["authority"] == "ADVISORY_ONLY"
    assert payload["result"]["model"] == "test-model"
    assert "server-only-test-key" not in response.get_data(as_text=True)


def test_advisor_rejects_unknown_finding_before_provider_call(
    tmp_path,
    monkeypatch,
):
    app = _app(tmp_path)
    client = app.test_client()
    analysis_id, _ = _create_analysis(client)

    def must_not_run(*args, **kwargs):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr(
        "app.routes.CodexAdvisor.advise",
        must_not_run,
    )
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/advisor",
        json={"finding_id": "missing"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "FINDING_NOT_FOUND"


def test_advisor_fails_closed_when_server_configuration_is_disabled(
    tmp_path,
):
    app = _app(
        tmp_path,
        CODEX_ADVISOR_ENABLED=False,
        OPENAI_API_KEY="",
        OPENAI_MODEL="",
    )
    client = app.test_client()
    analysis_id, finding_id = _create_analysis(client)

    response = client.post(
        f"/api/v1/analyses/{analysis_id}/advisor",
        json={"finding_id": finding_id},
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "AI_ADVISOR_UNAVAILABLE"


def test_advisor_requires_a_valid_request_body(tmp_path):
    app = _app(tmp_path)
    client = app.test_client()
    analysis_id, _ = _create_analysis(client)

    response = client.post(
        f"/api/v1/analyses/{analysis_id}/advisor",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_REQUEST"
