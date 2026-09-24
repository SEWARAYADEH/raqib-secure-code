from app.framework_intelligence import understand_frameworks
from app.parser_engine import parse_source


def test_flask_framework_route_and_auth_are_evidence_backed():
    parsed = parse_source(
        '''
from flask import Flask

app = Flask(__name__)

@app.get("/users/<int:user_id>")
@login_required
def get_user(user_id):
    return service.load(user_id)
'''.strip(),
        "Python",
    )
    understanding = understand_frameworks(parsed)

    assert understanding["frameworks"] == [
        {
            "name": "Flask",
            "category": "WEB_API",
            "status": "CORROBORATED",
            "evidence": ["IMPORT", "CALL", "DECORATOR"],
        }
    ]
    assert understanding["routes"][0]["path"] == (
        "/users/<int:user_id>"
    )
    assert understanding["routes"][0]["methods"] == ["GET"]
    assert understanding["routes"][0]["handler"] == "get_user"
    assert understanding["authentication_controls"][0][
        "effectiveness"
    ] == "UNVERIFIED"


def test_flask_import_without_runtime_evidence_is_candidate():
    parsed = parse_source(
        "from flask import request\n",
        "Python",
    )

    framework = understand_frameworks(parsed)["frameworks"][0]
    assert framework["status"] == "CANDIDATE"
    assert framework["evidence"] == ["IMPORT"]


def test_express_route_is_extracted_from_ast_call():
    parsed = parse_source(
        '''
import express from "express";
const app = express();
app.post("/login", loginHandler);
'''.strip(),
        "JavaScript",
    )
    understanding = understand_frameworks(parsed)

    assert understanding["frameworks"][0]["name"] == "Express"
    assert understanding["frameworks"][0]["status"] == (
        "CORROBORATED"
    )
    assert understanding["routes"][0]["path"] == "/login"
    assert understanding["routes"][0]["methods"] == ["POST"]
    assert understanding["routes"][0]["handler"] == "loginHandler"


def test_react_is_detected_from_import_evidence():
    parsed = parse_source(
        'import React from "react";\nconst value = 1;\n',
        "JavaScript",
    )
    understanding = understand_frameworks(parsed)

    assert understanding["project_role"] == "FRONTEND_COMPONENT"
    assert understanding["frameworks"][0]["name"] == "React"


def test_unknown_code_remains_unknown():
    parsed = parse_source(
        "def add(left, right):\n    return left + right\n",
        "Python",
    )
    understanding = understand_frameworks(parsed)

    assert understanding["project_role"] == "UNKNOWN_COMPONENT"
    assert understanding["frameworks"] == []
    assert understanding["routes"] == []
