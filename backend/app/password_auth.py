"""Password sign-in for addresses first verified through an email challenge."""

from __future__ import annotations

import hashlib
import hmac
import re
import sqlite3
import time
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


_DUMMY_HASH = generate_password_hash("not-a-real-password", method="scrypt:32768:8:1")
_EMAIL = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,253}$")


class PasswordPolicyError(ValueError):
    pass


class PasswordAuthenticationError(ValueError):
    pass


class PasswordStore:
    """A private SQLite credential store with persistent login throttling."""

    def __init__(self, database_path: str, rate_key: str) -> None:
        self.database_path = Path(database_path).resolve()
        self._rate_key = rate_key.encode("utf-8")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS password_accounts (
                email TEXT PRIMARY KEY, password_hash TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS password_attempts (
                attempt_key TEXT PRIMARY KEY, failures INTEGER NOT NULL,
                locked_until INTEGER NOT NULL
            )""")

    def set_password(
        self, email: str, password: str, current_password: str = "", *,
        allow_verified_email_reset: bool = False,
    ) -> None:
        normalized = _normalize_email(email)
        _validate_password(password)
        with self._connect() as db:
            row = db.execute(
                "SELECT password_hash FROM password_accounts WHERE email = ?", (normalized,)
            ).fetchone()
            if row is not None and not allow_verified_email_reset and not check_password_hash(
                row["password_hash"], current_password
            ):
                raise PasswordAuthenticationError("Current password is incorrect.")
            password_hash = generate_password_hash(password, method="scrypt:32768:8:1")
            db.execute(
                "INSERT INTO password_accounts (email, password_hash) VALUES (?, ?) "
                "ON CONFLICT(email) DO UPDATE SET password_hash = excluded.password_hash",
                (normalized, password_hash),
            )

    def authenticate(self, email: str, password: str, remote_address: str) -> bool:
        try:
            normalized = _normalize_email(email)
        except PasswordPolicyError:
            normalized = "invalid@example.invalid"
        if not isinstance(password, str) or len(password) > 1024:
            password = ""
        attempt_key = hmac.new(
            self._rate_key, f"{normalized}\0{remote_address}".encode(), hashlib.sha256
        ).hexdigest()
        now = int(time.time())
        with self._connect() as db:
            attempt = db.execute(
                "SELECT failures, locked_until FROM password_attempts WHERE attempt_key = ?",
                (attempt_key,),
            ).fetchone()
            if attempt is not None and attempt["locked_until"] > now:
                return False
            row = db.execute(
                "SELECT password_hash FROM password_accounts WHERE email = ?", (normalized,)
            ).fetchone()
            verified = check_password_hash(row["password_hash"] if row else _DUMMY_HASH, password)
            if verified and row is not None:
                db.execute("DELETE FROM password_attempts WHERE attempt_key = ?", (attempt_key,))
                return True
            failures = (attempt["failures"] if attempt else 0) + 1
            locked_until = now + 900 if failures >= 5 else 0
            db.execute(
                "INSERT INTO password_attempts (attempt_key, failures, locked_until) "
                "VALUES (?, ?, ?) ON CONFLICT(attempt_key) DO UPDATE SET "
                "failures = excluded.failures, locked_until = excluded.locked_until",
                (attempt_key, 0 if locked_until else failures, locked_until),
            )
            return False

    def has_password(self, email: str) -> bool:
        normalized = _normalize_email(email)
        with self._connect() as db:
            return db.execute(
                "SELECT 1 FROM password_accounts WHERE email = ?", (normalized,)
            ).fetchone() is not None

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database_path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("PRAGMA synchronous = FULL")
        return db


def _normalize_email(email: str) -> str:
    if not isinstance(email, str):
        raise PasswordPolicyError("Invalid email.")
    normalized = email.strip().casefold()
    if len(normalized) > 320 or not _EMAIL.fullmatch(normalized):
        raise PasswordPolicyError("Invalid email.")
    return normalized


def _validate_password(password: str) -> None:
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise PasswordPolicyError("Use a password between 12 and 128 characters.")
    if not (re.search(r"[a-z]", password) and re.search(r"[A-Z]", password)
            and re.search(r"\d", password) and re.search(r"[^A-Za-z0-9]", password)):
        raise PasswordPolicyError("Use upper/lowercase letters, a number, and a symbol.")
