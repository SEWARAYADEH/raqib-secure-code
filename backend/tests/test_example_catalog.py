"""Public examples must come from evaluated fixtures and exclude source code."""

import json
from pathlib import Path

from app import create_app
from app.example_catalog import ExampleCatalog


CASES = Path(__file__).resolve().parents[2] / "training/cases/sql_injection.json"


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
    assert len(examples) == 7
    assert database.is_file()
    assert all(set(item) == {
        "id", "classification", "candidate_count", "non_candidate_count", "source_sha256"
    } for item in examples)
    assert sum(item["candidate_count"] for item in examples) == 2
    assert {item["id"] for item in examples} >= {
        "javascript_sql_template_candidate",
        "javascript_sql_bound_parameter",
    }
    assert "SELECT * FROM users" not in response.get_data(as_text=True)

    restarted = create_app(settings)
    assert restarted.test_client().get("/api/v1/examples").json["examples"] == examples


def test_new_reference_cases_are_added_without_replacing_existing_rows(tmp_path):
    old_cases = tmp_path / "old_cases.json"
    old_cases.write_text(
        json.dumps(json.loads(CASES.read_text(encoding="utf-8"))[:5]),
        encoding="utf-8",
    )
    database = tmp_path / "examples.sqlite3"
    catalog = ExampleCatalog(str(database))
    assert catalog.seed_from_cases(old_cases) == 5
    original = catalog.list_examples()

    assert catalog.seed_from_cases(CASES) == 2
    assert len(catalog.list_examples()) == 7
    assert catalog.seed_from_cases(CASES) == 0
    assert all(item in catalog.list_examples() for item in original)
