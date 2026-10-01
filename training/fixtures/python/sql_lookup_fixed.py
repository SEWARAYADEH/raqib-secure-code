"""Trusted reference fix: SQLite parameter binding keeps input out of SQL text."""

from flask import request


def lookup_user(connection):
    user_id = request.args.get("id")
    return connection.execute(
        "SELECT name FROM users WHERE id = ?", (user_id,)
    ).fetchone()
