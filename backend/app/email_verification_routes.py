from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from app.api_errors import api_error
from app.auth import (
    SCOPE_ANALYSIS_CREATE,
    SCOPE_ANALYSIS_READ,
    trusted_frontend_origin,
)
import secrets

from app.email_verification import (
    AddressNotAllowed,
    ChallengeRejected,
    DeliveryUnavailable,
)


email_verification_api = Blueprint("email_verification_api", __name__)


@email_verification_api.post("/api/v1/auth/email-challenges")
def create_email_challenge():
    if not trusted_frontend_origin():
        return api_error(
            status_code=403,
            code="UNTRUSTED_REQUEST_ORIGIN",
            message="The request origin is not allowed.",
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("email"), str):
        return api_error(
            status_code=400,
            code="INVALID_REQUEST",
            message="A valid JSON request with an email field is required.",
        )

    try:
        receipt = _service().issue(payload["email"])
    except AddressNotAllowed:
        # Keep the public response indistinguishable from an accepted address.
        return (
            jsonify(
                {
                    "challenge_id": secrets.token_urlsafe(32),
                    "expires_in_seconds": 600,
                }
            ),
            201,
        )
    except ChallengeRejected as error:
        return api_error(
            status_code=429,
            code="CHALLENGE_REJECTED",
            message=str(error),
        )
    except DeliveryUnavailable:
        return api_error(
            status_code=503,
            code="EMAIL_DELIVERY_UNAVAILABLE",
            message="Verification email delivery is not configured or is unavailable.",
        )

    return (
        jsonify(
            {
                "challenge_id": receipt.challenge_id,
                "expires_in_seconds": receipt.expires_in_seconds,
            }
        ),
        201,
    )


@email_verification_api.post("/api/v1/auth/email-challenges/verify")
def verify_email_challenge():
    if not trusted_frontend_origin():
        return api_error(
            status_code=403,
            code="UNTRUSTED_REQUEST_ORIGIN",
            message="The request origin is not allowed.",
        )
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error(
            status_code=400,
            code="INVALID_REQUEST",
            message="A valid JSON request is required.",
        )

    challenge_id = payload.get("challenge_id")
    code = payload.get("code")
    if not isinstance(challenge_id, str) or not isinstance(code, str):
        return api_error(
            status_code=400,
            code="INVALID_REQUEST",
            message="challenge_id and code are required.",
        )

    try:
        verified_email = _service().verify(challenge_id, code)
    except ChallengeRejected as error:
        return api_error(
            status_code=401,
            code="VERIFICATION_FAILED",
            message=str(error),
        )

    session.clear()
    session["principal"] = {
        "subject": verified_email,
        "role": "VERIFIED_USER",
        "scopes": [SCOPE_ANALYSIS_CREATE, SCOPE_ANALYSIS_READ],
    }
    session.permanent = True
    return jsonify({"verified": True, "email": verified_email})


@email_verification_api.get("/api/v1/auth/session")
def get_session():
    principal = session.get("principal")
    if not isinstance(principal, dict):
        return api_error(
            status_code=401,
            code="SESSION_NOT_AUTHENTICATED",
            message="No authenticated session exists.",
        )
    return jsonify(
        {
            "authenticated": True,
            "principal": {
                "subject": principal.get("subject"),
                "role": principal.get("role"),
            },
        }
    )


@email_verification_api.post("/api/v1/auth/logout")
def logout():
    if not trusted_frontend_origin():
        return api_error(
            status_code=403,
            code="UNTRUSTED_REQUEST_ORIGIN",
            message="The request origin is not allowed.",
        )
    session.clear()
    return jsonify({"authenticated": False})


def _service():
    return current_app.extensions["email_challenge_service"]
