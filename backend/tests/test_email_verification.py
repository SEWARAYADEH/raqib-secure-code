from __future__ import annotations

import io
import pytest

from app import create_app
from app.email_verification import ChallengeRejected, EmailChallengeService


KEY = "v" * 32
ORIGIN = {"Origin": "http://localhost:5173"}


def test_challenge_sends_code_and_accepts_it_once():
    deliveries = []
    service = _service(deliveries)

    receipt = service.issue(" User@Example.com ")
    recipient, code, ttl = deliveries[0]

    assert recipient == "user@example.com"
    assert len(code) == 6
    assert ttl == 600
    assert service.verify(receipt.challenge_id, code) == "user@example.com"
    with pytest.raises(ChallengeRejected):
        service.verify(receipt.challenge_id, code)


def test_challenge_locks_after_failed_attempt_limit():
    deliveries = []
    service = _service(deliveries, max_attempts=2)
    receipt = service.issue("user@example.com")
    correct_code = deliveries[0][1]

    with pytest.raises(ChallengeRejected):
        service.verify(receipt.challenge_id, "000000")
    with pytest.raises(ChallengeRejected):
        service.verify(receipt.challenge_id, "000001")
    with pytest.raises(ChallengeRejected):
        service.verify(receipt.challenge_id, correct_code)


def test_challenge_expires_without_exposing_code():
    deliveries = []
    clock = [100.0]
    service = _service(deliveries, clock=lambda: clock[0], ttl_seconds=10)
    receipt = service.issue("user@example.com")
    code = deliveries[0][1]
    assert code not in repr(service._challenges)

    clock[0] = 111.0
    with pytest.raises(ChallengeRejected):
        service.verify(receipt.challenge_id, code)


def test_api_issues_and_verifies_challenge():
    deliveries = []
    app = _app_with_service(_service(deliveries))
    client = app.test_client()

    issued = client.post(
        "/api/v1/auth/email-challenges",
        json={"email": "user@example.com"},
        headers=ORIGIN,
    )
    assert issued.status_code == 201
    challenge_id = issued.get_json()["challenge_id"]

    verified = client.post(
        "/api/v1/auth/email-challenges/verify",
        json={"challenge_id": challenge_id, "code": deliveries[0][1]},
        headers=ORIGIN,
    )
    assert verified.status_code == 200
    assert verified.get_json() == {"verified": True, "email": "user@example.com"}


def test_api_does_not_reveal_disallowed_address():
    deliveries = []
    app = _app_with_service(_service(deliveries))
    response = app.test_client().post(
        "/api/v1/auth/email-challenges",
        json={"email": "unknown@example.com"},
        headers=ORIGIN,
    )

    assert response.status_code == 201
    assert len(response.get_json()["challenge_id"]) >= 32
    assert deliveries == []


def test_verified_email_creates_signed_session_for_remote_analysis():
    deliveries = []
    app = _app_with_service(_service(deliveries))
    app.config["ANALYSIS_LOCAL_ONLY"] = False
    client = app.test_client()
    issued = client.post(
        "/api/v1/auth/email-challenges",
        json={"email": "user@example.com"},
        headers=ORIGIN,
    )
    verified = client.post(
        "/api/v1/auth/email-challenges/verify",
        json={
            "challenge_id": issued.get_json()["challenge_id"],
            "code": deliveries[0][1],
        },
        headers=ORIGIN,
    )
    assert verified.status_code == 200

    response = client.post(
        "/api/v1/analysis/source",
        data={"file": (io.BytesIO(b"print('ok')\n"), "a.py")},
        content_type="multipart/form-data",
        headers=ORIGIN,
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )
    assert response.status_code == 200
    assert response.get_json()["principal"] == {
        "subject": "user@example.com",
        "role": "VERIFIED_USER",
    }


def test_session_authenticated_post_rejects_untrusted_origin():
    deliveries = []
    app = _app_with_service(_service(deliveries))
    app.config["ANALYSIS_LOCAL_ONLY"] = False
    client = app.test_client()
    issued = client.post(
        "/api/v1/auth/email-challenges",
        json={"email": "user@example.com"},
        headers=ORIGIN,
    )
    client.post(
        "/api/v1/auth/email-challenges/verify",
        json={
            "challenge_id": issued.get_json()["challenge_id"],
            "code": deliveries[0][1],
        },
        headers=ORIGIN,
    )

    response = client.post(
        "/api/v1/analysis/source",
        headers={"Origin": "https://attacker.example"},
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )
    assert response.status_code == 401


def _service(deliveries, **overrides):
    options = {
        "hmac_key": KEY,
        "sender": "sender@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 465,
        "smtp_username": "sender@example.com",
        "smtp_password": "secret",
        "allowed_emails": frozenset({"user@example.com"}),
        "minimum_resend_seconds": 0,
        "mail_sender": lambda email, code, ttl: deliveries.append((email, code, ttl)),
    }
    options.update(overrides)
    return EmailChallengeService(**options)


def _app_with_service(service):
    app = create_app(
        {
            "TESTING": True,
            "EMAIL_VERIFICATION_ENABLED": True,
            "EMAIL_VERIFICATION_HMAC_KEY": KEY,
            "VERIFICATION_ALLOWED_EMAILS": "user@example.com",
        }
    )
    app.extensions["email_challenge_service"] = service
    return app
