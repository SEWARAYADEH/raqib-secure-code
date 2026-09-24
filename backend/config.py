import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = False
    TESTING = False
    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    ANALYSIS_API_TOKEN = os.getenv(
        "ANALYSIS_API_TOKEN"
    )
    ANALYSIS_TOKEN_SUBJECT = os.getenv(
        "ANALYSIS_TOKEN_SUBJECT",
        "analysis-service",
    )
    ANALYSIS_LOCAL_ONLY = os.getenv(
        "ANALYSIS_LOCAL_ONLY",
        "true",
    ).lower() == "true"
    ANALYSIS_STORE_ENABLED = os.getenv(
        "ANALYSIS_STORE_ENABLED",
        "false",
    ).lower() == "true"
    ANALYSIS_DATABASE_PATH = os.getenv(
        "ANALYSIS_DATABASE_PATH"
    )
    RECORD_INTEGRITY_KEY = os.getenv(
        "RECORD_INTEGRITY_KEY"
    )
    WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT")
    EMAIL_VERIFICATION_ENABLED = os.getenv(
        "EMAIL_VERIFICATION_ENABLED",
        "true",
    ).lower() == "true"
    EMAIL_VERIFICATION_HMAC_KEY = os.getenv(
        "EMAIL_VERIFICATION_HMAC_KEY",
    )
    VERIFICATION_ALLOWED_EMAILS = os.getenv(
        "VERIFICATION_ALLOWED_EMAILS",
        "",
    )
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER = os.getenv("SMTP_SENDER", "")
    ISOLATION_RUNTIME_AVAILABLE = os.getenv(
        "ISOLATION_RUNTIME_AVAILABLE",
        "false",
    ).lower() == "true"
    CODEX_ADVISOR_ENABLED = os.getenv(
        "CODEX_ADVISOR_ENABLED",
        "false",
    ).lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
    CODEX_CONTEXT_MAX_CHARACTERS = int(
        os.getenv("CODEX_CONTEXT_MAX_CHARACTERS", "6000")
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    PERMANENT_SESSION_LIFETIME = 30 * 60
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024 + 64 * 1024
