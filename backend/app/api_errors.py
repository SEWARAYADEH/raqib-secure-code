from __future__ import annotations

from flask import g, jsonify
from werkzeug.exceptions import RequestEntityTooLarge


def api_error(
    *,
    status_code: int,
    code: str,
    message: str,
):
    return (
        jsonify(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": g.get("request_id"),
                }
            }
        ),
        status_code,
    )


def register_api_error_handlers(app) -> None:
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(_error):
        return api_error(
            status_code=413,
            code="REQUEST_TOO_LARGE",
            message="The request exceeds the configured upload limit.",
        )
