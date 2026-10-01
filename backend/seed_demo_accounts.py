"""Opt-in local demonstration account setup; never run in production."""

from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path

from dotenv import dotenv_values, set_key
from werkzeug.security import check_password_hash, generate_password_hash

from app.password_auth import PasswordStore


DEMO_CREDENTIALS = {
    "admin@securenergy.com": "Admin@12345",
    "user1@securenergy.com": "User@12345",
    "engineer@securenergy.com": "Eng@12345",
}


def seed_demo_accounts(database_path: Path, env_path: Path, *, app_env: str) -> int:
    if app_env.casefold() != "development":
        raise RuntimeError("Demo accounts are allowed only in development.")

    settings = dotenv_values(env_path) if env_path.exists() else {}
    if (settings.get("APP_ENV") or "development").casefold() != "development":
        raise RuntimeError("The local environment file is not in development mode.")

    secret_key = settings.get("SECRET_KEY") or ""
    if len(secret_key) < 32 or secret_key.casefold() in {"change_me", "changeme"}:
        secret_key = secrets.token_hex(32)
    verification_key = settings.get("EMAIL_VERIFICATION_HMAC_KEY") or ""
    if len(verification_key) < 32:
        verification_key = secrets.token_hex(32)

    PasswordStore(str(database_path), rate_key=secret_key)
    created = 0
    with sqlite3.connect(database_path) as database:
        for email, password in DEMO_CREDENTIALS.items():
            row = database.execute(
                "SELECT password_hash FROM password_accounts WHERE email = ?", (email,)
            ).fetchone()
            if row is not None:
                if not check_password_hash(row[0], password):
                    raise RuntimeError(f"Existing demo account has a different password: {email}")
                continue
            database.execute(
                "INSERT INTO password_accounts (email, password_hash) VALUES (?, ?)",
                (email, generate_password_hash(password, method="scrypt:32768:8:1")),
            )
            created += 1

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.touch(exist_ok=True)
    allowed = {
        address.strip().casefold()
        for address in (settings.get("VERIFICATION_ALLOWED_EMAILS") or "").split(",")
        if address.strip()
    }
    allowed.update(DEMO_CREDENTIALS)
    set_key(str(env_path), "APP_ENV", "development")
    set_key(str(env_path), "SECRET_KEY", secret_key)
    set_key(str(env_path), "EMAIL_VERIFICATION_HMAC_KEY", verification_key)
    set_key(str(env_path), "VERIFICATION_ALLOWED_EMAILS", ",".join(sorted(allowed)))
    return created


def main() -> None:
    backend = Path(__file__).resolve().parent
    env_path = backend / ".env"
    settings = dotenv_values(env_path) if env_path.exists() else {}
    database_path = Path(settings.get("AUTH_DATABASE_PATH") or backend / "instance" / "auth_accounts.sqlite3")
    environment = os.environ.get("APP_ENV") or settings.get("APP_ENV") or "development"
    created = seed_demo_accounts(database_path, env_path, app_env=environment)
    print(f"Local demo accounts ready: {len(DEMO_CREDENTIALS)}; newly created: {created}.")


if __name__ == "__main__":
    main()
