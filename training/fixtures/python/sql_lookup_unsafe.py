"""Trusted test fixture only: deliberately unsafe SQL construction."""

from flask import request


def lookup_user(connection):
    user_id = request.args.get("id")
    return connection.execute(
        f"SELECT name FROM users WHERE id = {user_id}"
    ).fetchone()
