"""Token-protected Gmail SMTP endpoint for explicitly allowed recipients."""

from __future__ import annotations

import hmac
import re

from flask import Blueprint, current_app, jsonify, request
from flask_mail import Mail, Message


mail = Mail()
mail_sender_api = Blueprint("mail_sender_api", __name__)
_EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+\Z")


@mail_sender_api.post("/send")
def send_email():
    """Send one plain-text message; SMTP acceptance is not inbox delivery proof."""
    config = current_app.config
    if not config["MAIL_SEND_ENABLED"]:
        return jsonify({"error": "Mail sending is unavailable."}), 503

    authorization = request.headers.get("Authorization", "")
    expected = f"Bearer {config['MAIL_SEND_API_TOKEN']}"
    if not hmac.compare_digest(authorization, expected):
        return jsonify({"error": "Unauthorized."}), 401

    if not request.is_json:
        return jsonify({"error": "A JSON request is required."}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    recipient = payload.get("to")
    subject = payload.get("subject")
    body = payload.get("body")
    if not isinstance(recipient, str) or not _EMAIL.fullmatch(recipient) or len(recipient) > 254:
        return jsonify({"error": "A valid recipient email is required."}), 400
    if not isinstance(subject, str) or not 1 <= len(subject) <= 200 or "\n" in subject or "\r" in subject:
        return jsonify({"error": "A valid subject is required."}), 400
    if not isinstance(body, str) or not 1 <= len(body) <= 10000:
        return jsonify({"error": "A plain-text body is required."}), 400

    allowed = {
        address.strip().casefold()
        for address in config["MAIL_ALLOWED_RECIPIENTS"].split(",")
        if address.strip()
    }
    if recipient.casefold() not in allowed:
        return jsonify({"error": "Recipient is not allowed."}), 403

    message = Message(
        subject=subject,
        recipients=[recipient],
        body=body,
        sender=("Raqeeb", config["EMAIL_USER"]),
    )
    try:
        mail.send(message)
    except Exception as error:
        current_app.logger.warning("SMTP send failed: %s", type(error).__name__)
        return jsonify({"error": "The email could not be sent."}), 500
    return jsonify({"status": "accepted_by_smtp", "recipient": recipient}), 200
