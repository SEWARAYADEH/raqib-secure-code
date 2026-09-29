"""Password login must follow verified email and survive a new client session."""

import sqlite3

from app import create_app
from app.email_verification import EmailChallengeService


ORIGIN = {"Origin": "http://localhost:5173"}
PASSWORD = "Strong-Example-2026!"


def _app(tmp_path):
    deliveries = []
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "s" * 32,
        "AUTH_DATABASE_PATH": str(tmp_path / "auth.sqlite3"),
        "EMAIL_VERIFICATION_ENABLED": True,
        "EMAIL_VERIFICATION_HMAC_KEY": "v" * 32,
        "VERIFICATION_ALLOWED_EMAILS": "user@example.com",
    })
    app.extensions["email_challenge_service"] = EmailChallengeService(
        hmac_key="v" * 32,
        sender="sender@example.com",
        smtp_host="smtp.example.com",
        smtp_port=465,
        smtp_username="sender@example.com",
        smtp_password="unused",
        allowed_emails=frozenset({"user@example.com"}),
        mail_sender=lambda email, code, ttl: deliveries.append(code),
    )
    return app, deliveries


def _verify_email(client, deliveries):
    issued = client.post(
        "/api/v1/auth/email-challenges",
        json={"email": "user@example.com"},
        headers=ORIGIN,
    )
    assert issued.status_code == 201
    verified = client.post(
        "/api/v1/auth/email-challenges/verify",
        json={"challenge_id": issued.json["challenge_id"], "code": deliveries[-1]},
        headers=ORIGIN,
    )
    assert verified.status_code == 200


def test_password_setup_and_new_session_login(tmp_path):
    app, deliveries = _app(tmp_path)
    client = app.test_client()
    _verify_email(client, deliveries)
    assert client.get("/api/v1/auth/session").json["password_configured"] is False

    setup = client.post(
        "/api/v1/auth/password/setup", json={"password": PASSWORD}, headers=ORIGIN
    )
    assert setup.status_code == 200
    assert client.get("/api/v1/auth/session").json["password_configured"] is True
    assert client.get("/api/v1/auth/session").json["password_reset_allowed"] is False

    with sqlite3.connect(tmp_path / "auth.sqlite3") as db:
        stored = db.execute("SELECT password_hash FROM password_accounts").fetchone()[0]
    assert PASSWORD not in stored
    assert stored.startswith("scrypt:")

    separate_browser = app.test_client()
    signed_in = separate_browser.post(
        "/api/v1/auth/password",
        json={"email": "USER@example.com", "password": PASSWORD},
        headers=ORIGIN,
    )
    assert signed_in.status_code == 200
    assert separate_browser.get("/api/v1/auth/session").json["principal"]["subject"] == "user@example.com"
    assert separate_browser.get("/api/v1/auth/session").json["password_reset_allowed"] is False


def test_password_login_rejects_wrong_password_and_untrusted_origin(tmp_path):
    app, deliveries = _app(tmp_path)
    client = app.test_client()
    _verify_email(client, deliveries)
    client.post("/api/v1/auth/password/setup", json={"password": PASSWORD}, headers=ORIGIN)
    other = app.test_client()
    assert other.post(
        "/api/v1/auth/password", json={"email": "user@example.com", "password": "wrong"},
        headers=ORIGIN,
    ).status_code == 401
    assert other.post(
        "/api/v1/auth/password", json={"email": "user@example.com", "password": PASSWORD},
        headers={"Origin": "https://attacker.example"},
    ).status_code == 403


def test_password_change_requires_old_password_after_email_window(tmp_path):
    app, deliveries = _app(tmp_path)
    client = app.test_client()
    _verify_email(client, deliveries)
    assert client.post(
        "/api/v1/auth/password/setup", json={"password": PASSWORD}, headers=ORIGIN
    ).status_code == 200
    replacement = "New-Example-Password-2026!"
    assert client.post(
        "/api/v1/auth/password/setup", json={"password": replacement}, headers=ORIGIN
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/password/setup",
        json={"password": replacement, "current_password": PASSWORD},
        headers=ORIGIN,
    ).status_code == 200
    assert app.test_client().post(
        "/api/v1/auth/password",
        json={"email": "user@example.com", "password": replacement}, headers=ORIGIN,
    ).status_code == 200


def test_deauthorized_address_cannot_use_existing_password(tmp_path):
    app, deliveries = _app(tmp_path)
    client = app.test_client()
    _verify_email(client, deliveries)
    client.post("/api/v1/auth/password/setup", json={"password": PASSWORD}, headers=ORIGIN)
    app.config["VERIFICATION_ALLOWED_EMAILS"] = "another@example.com"
    assert client.get("/api/v1/auth/session").status_code == 401
    assert app.test_client().post(
        "/api/v1/auth/password",
        json={"email": "user@example.com", "password": PASSWORD}, headers=ORIGIN,
    ).status_code == 401
