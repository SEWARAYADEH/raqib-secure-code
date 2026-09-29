"""Public examples must come from evaluated fixtures and exclude source code."""

from app import create_app


def test_synthetic_examples_are_persisted_and_read_only(tmp_path):
    database = tmp_path / "examples.sqlite3"
    settings = {
        "TESTING": True,
        "AUTH_DATABASE_PATH": str(tmp_path / "auth.sqlite3"),
        "EXAMPLE_DATABASE_PATH": str(database),
        "EMAIL_VERIFICATION_ENABLED": False,
    }
    app = create_app(settings)
    response = app.test_client().get("/api/v1/examples")
    assert response.status_code == 200
    examples = response.json["examples"]
    assert len(examples) == 5
    assert database.is_file()
    assert all(set(item) == {
        "id", "classification", "candidate_count", "non_candidate_count", "source_sha256"
    } for item in examples)
    assert sum(item["candidate_count"] for item in examples) == 1
    assert "SELECT * FROM users" not in response.get_data(as_text=True)

    restarted = create_app(settings)
    assert restarted.test_client().get("/api/v1/examples").json["examples"] == examples
