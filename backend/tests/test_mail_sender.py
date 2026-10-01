"""The optional Gmail sender must never become an unauthenticated relay."""

import pytest

from app import create_app
from app.mail_sender import mail


TOKEN = "m" * 40
PAYLOAD = {"to": "recipient@example.com", "subject": "Raqeeb report", "body": "Analysis completed."}


def _app(tmp_path):
    return create_app({
        "TESTING": True,
        "EMAIL_VERIFICATION_ENABLED": False,
        "AUTH_DATABASE_PATH": str(tmp_path / "auth.sqlite3"),
        "EXAMPLE_DATABASE_PATH": str(tmp_path / "examples.sqlite3"),
        "TRAINING_DATABASE_PATH": str(tmp_path / "training.sqlite3"),
        "MAIL_SEND_ENABLED": True,
        "MAIL_SEND_API_TOKEN": TOKEN,
        "MAIL_ALLOWED_RECIPIENTS": "recipient@example.com",
        "EMAIL_USER": "sender@gmail.com",
        "EMAIL_PASS": "test-only-app-password",
    })


def test_send_requires_token_and_allowlisted_recipient(tmp_path, monkeypatch):
    app = _app(tmp_path)
    sent = []
    monkeypatch.setattr(mail, "send", sent.append)
    client = app.test_client()

    assert client.post("/send", json=PAYLOAD).status_code == 401
    headers = {"Authorization": f"Bearer {TOKEN}"}
    assert client.post("/send", json={**PAYLOAD, "to": "other@example.com"}, headers=headers).status_code == 403
    assert client.post("/send", json={**PAYLOAD, "subject": "bad\r\nBcc: victim@example.com"}, headers=headers).status_code == 400
    assert sent == []

    response = client.post("/send", json=PAYLOAD, headers=headers)
    assert response.status_code == 200
    assert response.json["status"] == "accepted_by_smtp"
    assert len(sent) == 1
    assert sent[0].sender == "Raqeeb <sender@gmail.com>"
    assert sent[0].recipients == ["recipient@example.com"]
    assert app.config["MAIL_SERVER"] == "smtp.gmail.com"
    assert app.config["MAIL_PORT"] == 587
    assert app.config["MAIL_USE_TLS"] is True


def test_send_returns_generic_error_without_leaking_smtp_details(tmp_path, monkeypatch):
    app = _app(tmp_path)
    def fail(_message):
        raise RuntimeError("private SMTP detail")
    monkeypatch.setattr(mail, "send", fail)
    response = app.test_client().post(
        "/send", json=PAYLOAD, headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 500
    assert "private SMTP detail" not in response.get_data(as_text=True)


def test_sender_stays_disabled_until_complete_configuration(tmp_path):
    with pytest.raises(RuntimeError, match="strong API token"):
        create_app({"MAIL_SEND_ENABLED": True, "EMAIL_VERIFICATION_ENABLED": False})
