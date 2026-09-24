import io
import sqlite3

import pytest

from app import create_app


TOKEN = "t" * 40
INTEGRITY_KEY = "i" * 40


@pytest.fixture
def stored_app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "ANALYSIS_LOCAL_ONLY": True,
            "ANALYSIS_API_TOKEN": TOKEN,
            "ANALYSIS_TOKEN_SUBJECT": "test-service",
            "ANALYSIS_STORE_ENABLED": True,
            "ANALYSIS_DATABASE_PATH": str(
                tmp_path / "analyses.sqlite3"
            ),
            "RECORD_INTEGRITY_KEY": INTEGRITY_KEY,
        }
    )


def _create(client):
    return client.post(
        "/api/v1/analysis/source",
        data={
            "file": (
                io.BytesIO(b"print('safe')\n"),
                "example.py",
            )
        },
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {TOKEN}"},
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )


def test_completed_analysis_is_persisted_and_verified(stored_app):
    client = stored_app.test_client()
    created = _create(client)

    assert created.status_code == 200
    record = created.get_json()["record"]
    assert record["persisted"] is True
    assert record["integrity"] == "HMAC-SHA256"

    fetched = client.get(
        f'/api/v1/analyses/{record["analysis_id"]}',
        headers={"Authorization": f"Bearer {TOKEN}"},
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert fetched.status_code == 200
    assert fetched.get_json()["record"]["result"][
        "artifact"
    ]["filename"] == "example.py"


def test_record_owner_is_enforced(stored_app):
    client = stored_app.test_client()
    record = _create(client).get_json()["record"]

    response = client.get(
        f'/api/v1/analyses/{record["analysis_id"]}',
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == (
        "ANALYSIS_RECORD_FORBIDDEN"
    )


def test_tampered_record_is_rejected(stored_app):
    client = stored_app.test_client()
    record = _create(client).get_json()["record"]

    with sqlite3.connect(
        stored_app.config["ANALYSIS_DATABASE_PATH"]
    ) as connection:
        connection.execute(
            "UPDATE analysis_records SET result_json = ? "
            "WHERE analysis_id = ?",
            ("{}", record["analysis_id"]),
        )

    response = client.get(
        f'/api/v1/analyses/{record["analysis_id"]}',
        headers={"Authorization": f"Bearer {TOKEN}"},
        environ_base={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == (
        "ANALYSIS_INTEGRITY_FAILURE"
    )


def test_no_update_or_delete_api_is_exposed(stored_app):
    client = stored_app.test_client()
    record = _create(client).get_json()["record"]
    path = f'/api/v1/analyses/{record["analysis_id"]}'

    assert client.patch(path).status_code == 405
    assert client.delete(path).status_code == 405


def test_store_requires_strong_integrity_key(tmp_path):
    with pytest.raises(RuntimeError, match="strong"):
        create_app(
            {
                "ANALYSIS_STORE_ENABLED": True,
                "ANALYSIS_DATABASE_PATH": str(tmp_path / "db.sqlite3"),
                "RECORD_INTEGRITY_KEY": "weak",
            }
        )
