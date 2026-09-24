from __future__ import annotations

import hmac
import ipaddress
from dataclasses import dataclass

from flask import current_app, request, session


SCOPE_ANALYSIS_CREATE = "analysis:create"
SCOPE_ANALYSIS_READ = "analysis:read"


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str
    scopes: frozenset[str]
    authentication_method: str

    def permits(self, scope: str) -> bool:
        return scope in self.scopes


def resolve_analysis_principal() -> Principal | None:
    authorization = request.headers.get("Authorization", "")
    expected_token = current_app.config.get(
        "ANALYSIS_API_TOKEN"
    )

    if authorization:
        prefix = "Bearer "

        if not expected_token or not authorization.startswith(prefix):
            return None

        supplied_token = authorization[len(prefix) :]

        if not hmac.compare_digest(
            supplied_token,
            expected_token,
        ):
            return None

        return Principal(
            subject=current_app.config[
                "ANALYSIS_TOKEN_SUBJECT"
            ],
            role="ANALYSIS_SERVICE",
            scopes=frozenset(
                {
                    SCOPE_ANALYSIS_CREATE,
                    SCOPE_ANALYSIS_READ,
                }
            ),
            authentication_method="BEARER_TOKEN",
        )

    session_principal = session.get("principal")
    if isinstance(session_principal, dict):
        if not trusted_frontend_origin():
            return None
        subject = session_principal.get("subject")
        role = session_principal.get("role")
        scopes = session_principal.get("scopes")
        if (
            isinstance(subject, str)
            and isinstance(role, str)
            and isinstance(scopes, list)
            and all(isinstance(scope, str) for scope in scopes)
        ):
            return Principal(
                subject=subject,
                role=role,
                scopes=frozenset(scopes),
                authentication_method="SIGNED_SESSION",
            )

    if not current_app.config.get(
        "ANALYSIS_LOCAL_ONLY",
        True,
    ):
        return None

    try:
        address = ipaddress.ip_address(
            request.remote_addr or ""
        )
    except ValueError:
        return None

    if not address.is_loopback:
        return None

    return Principal(
        subject="local-developer",
        role="LOCAL_DEVELOPER",
        scopes=frozenset(
            {
                SCOPE_ANALYSIS_CREATE,
                SCOPE_ANALYSIS_READ,
            }
        ),
        authentication_method="LOOPBACK",
    )


def trusted_frontend_origin() -> bool:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return True
    origin = request.headers.get("Origin", "")
    allowed = {
        item.strip()
        for item in current_app.config["FRONTEND_ORIGIN"].split(",")
        if item.strip()
    }
    return origin in allowed
