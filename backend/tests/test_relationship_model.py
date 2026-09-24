from app.parser_engine import parse_source
from app.relationship_model import (
    RESOLUTION_LOCAL,
    RESOLUTION_UNRESOLVED,
    build_relationship_model,
)


def test_python_local_call_relationship():
    source = """
def sanitize(value):
    return value.strip()

def login(value):
    clean = sanitize(value)
    print(clean)
    return clean
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    model = build_relationship_model(
        parsed
    )

    relationships = {
        (
            item["caller"],
            item["callee"],
        )
        for item in model[
            "relationships"
        ]
    }

    assert (
        "login",
        "sanitize",
    ) in relationships


def test_python_method_relationship():
    source = """
class AuthService:
    def normalize(self, token):
        return token.strip()

    def validate(self, token):
        return self.normalize(token)
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    model = build_relationship_model(
        parsed
    )

    relationships = {
        (
            item["caller"],
            item["callee"],
        )
        for item in model[
            "relationships"
        ]
    }

    assert (
        "AuthService.validate",
        "AuthService.normalize",
    ) in relationships


def test_external_call_is_not_falsely_resolved():
    source = """
def get_user(user_id):
    return db.execute(user_id)
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    model = build_relationship_model(
        parsed
    )

    unresolved = [
        item
        for item in model[
            "unresolved_calls"
        ]
        if item["call_target"]
        == "db.execute"
    ]

    assert len(unresolved) == 1

    assert (
        unresolved[0]["resolution"]
        == RESOLUTION_UNRESOLVED
    )


def test_javascript_local_relationship():
    source = """
function sanitize(value) {
    return value.trim();
}

function login(value) {
    return sanitize(value);
}
""".strip()

    parsed = parse_source(
        source,
        "JavaScript",
    )

    model = build_relationship_model(
        parsed
    )

    relationships = {
        (
            item["caller"],
            item["callee"],
        )
        for item in model[
            "relationships"
        ]
    }

    assert (
        "login",
        "sanitize",
    ) in relationships


def test_module_level_call_is_separate():
    source = """
from flask import Flask

app = Flask(__name__)

def create_app():
    return app
""".strip()

    parsed = parse_source(
        source,
        "Python",
    )

    model = build_relationship_model(
        parsed
    )

    targets = {
        item["call_target"]
        for item in model[
            "module_calls"
        ]
    }

    assert "Flask" in targets
