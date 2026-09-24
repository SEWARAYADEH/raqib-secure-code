import io

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "ANALYSIS_LOCAL_ONLY": True,
            "ANALYSIS_API_TOKEN": None,
        }
    )
    return app.test_client()


def test_source_analysis_returns_structured_evidence(client):
    source = b'''from flask import request
import os

def run():
    command = request.args.get("command")
    os.system(command)
'''

    response = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(source), "example.py")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    result = payload["result"]

    assert result["schema_version"] == "1.0"
    assert result["analysis"] == {
        "execution_policy": "NEVER_EXECUTE_SOURCE",
        "finding_policy": "EVIDENCE_GATED_CANDIDATES",
        "scope": "FILE",
    }
    assert "source_text" not in result["artifact"]
    assert result["structure"]["counts"]["assignments"] == 1
    assert result["data_flow"]["counts"]["observed_paths"] == 1
    assert payload["request_id"]


def test_analysis_requires_exactly_one_file(client):
    response = client.post(
        "/api/v1/analysis/source",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == (
        "INVALID_FILE_COUNT"
    )


def test_analysis_rejects_unverified_language(client):
    response = client.post(
        "/api/v1/analysis/source",
        data={
            "file": (
                io.BytesIO(b"public class Example {}\n"),
                "Example.java",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == (
        "UNSUPPORTED_ANALYSIS_INPUT"
    )


def test_analysis_rejects_non_local_request_without_token(client):
    response = client.post(
        "/api/v1/analysis/source",
        data={
            "file": (
                io.BytesIO(b"print('safe')\n"),
                "example.py",
            )
        },
        content_type="multipart/form-data",
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == (
        "ANALYSIS_ACCESS_DENIED"
    )


def test_analysis_token_allows_authorized_remote_request():
    app = create_app(
        {
            "TESTING": True,
            "ANALYSIS_LOCAL_ONLY": False,
            "ANALYSIS_API_TOKEN": "test-analysis-token",
        }
    )
    client = app.test_client()

    response = client.post(
        "/api/v1/analysis/source",
        data={
            "file": (
                io.BytesIO(b"print('safe')\n"),
                "example.py",
            )
        },
        content_type="multipart/form-data",
        headers={
            "Authorization": "Bearer test-analysis-token"
        },
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 200


def test_security_headers_are_applied(client):
    response = client.get("/api/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"]


def test_oversized_request_uses_json_error_contract(client):
    response = client.post(
        "/api/v1/analysis/source",
        data={
            "file": (
                io.BytesIO(b"a" * (2 * 1024 * 1024 + 65 * 1024)),
                "large.py",
            )
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert response.is_json
    assert response.get_json()["error"]["code"] == (
        "SOURCE_FILE_TOO_LARGE"
    )


def test_production_configuration_fails_closed():
    with pytest.raises(
        RuntimeError,
        match=(
            "ANALYSIS_API_TOKEN, EMAIL_VERIFICATION_HMAC_KEY, "
            "RECORD_INTEGRITY_KEY, SECRET_KEY"
        ),
    ):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": None,
                "ANALYSIS_API_TOKEN": None,
                "EMAIL_VERIFICATION_HMAC_KEY": None,
                "RECORD_INTEGRITY_KEY": None,
            }
        )


def test_production_rejects_short_secrets():
    with pytest.raises(RuntimeError, match="missing or weak"):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": "short",
                "ANALYSIS_API_TOKEN": "also-short",
                "RECORD_INTEGRITY_KEY": "short-too",
            }
        )


def test_production_requires_immutable_storage():
    with pytest.raises(
        RuntimeError,
        match="immutable analysis storage",
    ):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": "s" * 40,
                "ANALYSIS_API_TOKEN": "t" * 40,
                "RECORD_INTEGRITY_KEY": "i" * 40,
                "EMAIL_VERIFICATION_HMAC_KEY": "e" * 40,
                "ANALYSIS_STORE_ENABLED": False,
            }
        )
