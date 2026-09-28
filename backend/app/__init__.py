from pathlib import Path
import secrets

from flask import Flask, abort, send_from_directory
from flask_cors import CORS

from config import Config
from app.api_errors import register_api_error_handlers
from app.analysis_store import AnalysisStore
from app.archive_routes import archive_api
from app.email_verification import EmailChallengeService
from app.email_verification_routes import email_verification_api
from app.http_security import register_http_security
from app.routes import api


def create_app(config_overrides: dict | None = None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if config_overrides:
        app.config.update(config_overrides)

    _validate_security_config(app)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    if not app.config.get("EMAIL_VERIFICATION_HMAC_KEY"):
        app.config["EMAIL_VERIFICATION_HMAC_KEY"] = secrets.token_hex(32)
    app.config["SESSION_COOKIE_SECURE"] = (
        app.config["APP_ENV"] == "production"
    )

    if app.config["ANALYSIS_STORE_ENABLED"]:
        database_path = app.config.get(
            "ANALYSIS_DATABASE_PATH"
        ) or str(Path(app.instance_path) / "analyses.sqlite3")
        app.extensions["analysis_store"] = AnalysisStore(
            database_path=database_path,
            integrity_key=app.config[
                "RECORD_INTEGRITY_KEY"
            ],
        )

    if app.config["EMAIL_VERIFICATION_ENABLED"]:
        allowed_emails = frozenset(
            email.strip().casefold()
            for email in app.config["VERIFICATION_ALLOWED_EMAILS"].split(",")
            if email.strip()
        )
        app.extensions["email_challenge_service"] = EmailChallengeService(
            hmac_key=app.config["EMAIL_VERIFICATION_HMAC_KEY"],
            sender=app.config["SMTP_SENDER"],
            smtp_host=app.config["SMTP_HOST"],
            smtp_port=app.config["SMTP_PORT"],
            smtp_username=app.config["SMTP_USERNAME"],
            smtp_password=app.config["SMTP_PASSWORD"],
            allowed_emails=allowed_emails,
            use_ssl=app.config["SMTP_USE_SSL"],
        )

    register_http_security(app)
    register_api_error_handlers(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": _frontend_origins(app),
            }
        },
        supports_credentials=True,
    )

    app.register_blueprint(api)
    app.register_blueprint(archive_api)
    if app.config["EMAIL_VERIFICATION_ENABLED"]:
        app.register_blueprint(email_verification_api)

    _register_frontend_routes(app)

    return app


def _frontend_origins(app) -> list[str]:
    return [
        origin.strip()
        for origin in app.config["FRONTEND_ORIGIN"].split(",")
        if origin.strip()
    ]


def _validate_security_config(app) -> None:
    if app.config["APP_ENV"] == "production":
        secrets = {
            "SECRET_KEY": app.config.get("SECRET_KEY"),
            "ANALYSIS_API_TOKEN": app.config.get("ANALYSIS_API_TOKEN"),
            "RECORD_INTEGRITY_KEY": app.config.get("RECORD_INTEGRITY_KEY"),
            "EMAIL_VERIFICATION_HMAC_KEY": app.config.get(
                "EMAIL_VERIFICATION_HMAC_KEY"
            ),
        }
        invalid = [
            name
            for name, value in secrets.items()
            if not isinstance(value, str)
            or len(value) < 32
            or value.lower() in {"change_me", "changeme"}
        ]
        if invalid:
            joined = ", ".join(sorted(invalid))
            raise RuntimeError(
                "Production security configuration is missing or weak: "
                f"{joined}"
            )
        if not app.config["ANALYSIS_STORE_ENABLED"]:
            raise RuntimeError("Production requires immutable analysis storage.")
        if app.config["EMAIL_VERIFICATION_ENABLED"] and not all(
            app.config.get(name)
            for name in (
                "SMTP_HOST",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "SMTP_SENDER",
            )
        ):
            raise RuntimeError(
                "Production email verification requires complete SMTP configuration."
            )
        if app.config["EMAIL_VERIFICATION_ENABLED"] and not app.config[
            "VERIFICATION_ALLOWED_EMAILS"
        ].strip():
            raise RuntimeError(
                "Production email verification requires an allowed address."
            )

    if app.config["ANALYSIS_STORE_ENABLED"]:
        integrity_key = app.config.get("RECORD_INTEGRITY_KEY")
        if not isinstance(integrity_key, str) or len(integrity_key) < 32:
            raise RuntimeError(
                "Immutable storage requires a strong RECORD_INTEGRITY_KEY."
            )


def _register_frontend_routes(app) -> None:
    configured = app.config.get("FRONTEND_DIST_PATH")
    frontend_dist = (
        Path(configured).resolve()
        if configured
        else (
            Path(__file__).resolve().parents[2]
            / "step-one-secure-code-ai-agent-frontend-professional"
            / "dist"
        ).resolve()
    )

    def serve_path(relative_path: str):
        if relative_path == "api" or relative_path.startswith("api/"):
            abort(404)

        candidate = (frontend_dist / relative_path).resolve()
        try:
            candidate.relative_to(frontend_dist)
        except ValueError:
            abort(404)

        if relative_path and candidate.is_file():
            return send_from_directory(frontend_dist, relative_path)

        index_file = frontend_dist / "index.html"
        if index_file.is_file():
            return send_from_directory(frontend_dist, "index.html")

        abort(404)

    app.add_url_rule(
        "/",
        endpoint="frontend_index",
        view_func=lambda: serve_path(""),
        methods=["GET"],
    )
    app.add_url_rule(
        "/<path:frontend_path>",
        endpoint="frontend_spa",
        view_func=serve_path,
        methods=["GET"],
    )
