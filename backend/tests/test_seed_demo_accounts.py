"""Public demo credentials must be reproducible locally and inert in production."""

import sqlite3

import pytest
from dotenv import dotenv_values
from werkzeug.security import check_password_hash

from seed_demo_accounts import DEMO_CREDENTIALS, seed_demo_accounts


def test_seed_is_local_idempotent_and_stores_only_hashes(tmp_path):
    database_path = tmp_path / "auth.sqlite3"
    env_path = tmp_path / ".env"
    assert seed_demo_accounts(database_path, env_path, app_env="development") == 3
    assert seed_demo_accounts(database_path, env_path, app_env="development") == 0
    settings = dotenv_values(env_path)
    assert set(settings["VERIFICATION_ALLOWED_EMAILS"].split(",")) == set(DEMO_CREDENTIALS)
    assert len(settings["SECRET_KEY"]) >= 32
    with sqlite3.connect(database_path) as database:
        rows = database.execute("SELECT email, password_hash FROM password_accounts").fetchall()
    assert len(rows) == 3
    assert all(hash_value.startswith("scrypt:") for _, hash_value in rows)
    assert all(check_password_hash(hash_value, DEMO_CREDENTIALS[email]) for email, hash_value in rows)
    assert all(password not in env_path.read_text(encoding="utf-8") for password in DEMO_CREDENTIALS.values())


def test_seed_refuses_production(tmp_path):
    with pytest.raises(RuntimeError, match="only in development"):
        seed_demo_accounts(tmp_path / "auth.sqlite3", tmp_path / ".env", app_env="production")
    assert not (tmp_path / "auth.sqlite3").exists()
