from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session
import time

from app.api_errors import api_error
from app.auth import (
    SCOPE_ANALYSIS_CREATE,
    SCOPE_ANALYSIS_READ,
    email_address_allowed,
    trusted_frontend_origin,
)
import secrets

from app.email_verification import (
    AddressNotAllowed,
    ChallengeRejected,
    DeliveryUnavailable,
)
from app.password_auth import PasswordAuthenticationError, PasswordPolicyError


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
            message="Verification email delivery is unavailable.",
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
    session["email_verified_at"] = int(time.time())
    session.permanent = True
    return jsonify({"verified": True, "email": verified_email})


@email_verification_api.post("/api/v1/auth/password")
def sign_in_with_password():
    if not trusted_frontend_origin():
        return api_error(status_code=403, code="UNTRUSTED_REQUEST_ORIGIN", message="The request origin is not allowed.")
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error(status_code=400, code="INVALID_REQUEST", message="Email and password are required.")
    email, password = payload.get("email"), payload.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return api_error(status_code=400, code="INVALID_REQUEST", message="Email and password are required.")
    normalized_email = email.strip().casefold()
    store = current_app.extensions["password_store"]
    authenticated = store.authenticate(email, password, request.remote_addr or "")
    if not authenticated or not email_address_allowed(normalized_email):
        return api_error(status_code=401, code="PASSWORD_AUTH_FAILED", message="Email or password is invalid.")
    session.clear()
    session["principal"] = {
        "subject": normalized_email,
        "role": "VERIFIED_USER",
        "scopes": [SCOPE_ANALYSIS_CREATE, SCOPE_ANALYSIS_READ],
    }
    session.permanent = True
    return jsonify({"authenticated": True, "email": normalized_email})


@email_verification_api.post("/api/v1/auth/password/setup")
def set_account_password():
    if not trusted_frontend_origin():
        return api_error(status_code=403, code="UNTRUSTED_REQUEST_ORIGIN", message="The request origin is not allowed.")
    principal = session.get("principal")
    if not isinstance(principal, dict) or not isinstance(principal.get("subject"), str):
        return api_error(status_code=401, code="SESSION_NOT_AUTHENTICATED", message="A verified session is required.")
    if not email_address_allowed(principal["subject"]):
        session.clear()
        return api_error(status_code=401, code="SESSION_NOT_AUTHENTICATED", message="A verified session is required.")
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return api_error(status_code=400, code="INVALID_REQUEST", message="Password fields are required.")
    password = payload.get("password")
    current_password = payload.get("current_password", "")
    if not isinstance(password, str) or not isinstance(current_password, str):
        return api_error(status_code=400, code="INVALID_REQUEST", message="Password fields are required.")
    try:
        verified_at = session.get("email_verified_at")
        allow_reset = (
            isinstance(verified_at, int)
            and 0 <= int(time.time()) - verified_at <= 600
        )
        current_app.extensions["password_store"].set_password(
            principal["subject"], password, current_password,
            allow_verified_email_reset=allow_reset and not current_password,
        )
    except PasswordPolicyError as error:
        return api_error(status_code=400, code="PASSWORD_POLICY_REJECTED", message=str(error))
    except PasswordAuthenticationError:
        return api_error(status_code=401, code="CURRENT_PASSWORD_INVALID", message="Current password is invalid.")
    session.pop("email_verified_at", None)
    return jsonify({"password_configured": True})


@email_verification_api.get("/api/v1/auth/session")
def get_session():
    principal = session.get("principal")
    if not isinstance(principal, dict):
        return api_error(
            status_code=401,
            code="SESSION_NOT_AUTHENTICATED",
            message="No authenticated session exists.",
        )
    if not email_address_allowed(principal.get("subject")):
        session.clear()
        return api_error(status_code=401, code="SESSION_NOT_AUTHENTICATED", message="No authenticated session exists.")
    return jsonify(
        {
            "authenticated": True,
            "principal": {
                "subject": principal.get("subject"),
                "role": principal.get("role"),
            },
            "password_configured": current_app.extensions["password_store"].has_password(
                principal["subject"]
            ),
            "password_reset_allowed": isinstance(session.get("email_verified_at"), int)
            and 0 <= int(time.time()) - session["email_verified_at"] <= 600,
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
