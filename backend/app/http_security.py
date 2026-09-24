from __future__ import annotations

import uuid

from flask import g, request


def register_http_security(app) -> None:
    @app.before_request
    def assign_request_id():
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = (
            supplied
            if _valid_request_id(supplied)
            else str(uuid.uuid4())
        )

    @app.after_request
    def apply_security_headers(response):
        response.headers["X-Request-ID"] = g.get(
            "request_id",
            str(uuid.uuid4()),
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'none'; frame-ancestors 'none'"
        return response


def _valid_request_id(value: str) -> bool:
    return (
        1 <= len(value) <= 128
        and all(
            character.isalnum()
            or character in {"-", "_", "."}
            for character in value
        )
    )
