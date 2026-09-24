import pytest

from app.parser_engine import (
    UnsupportedParserLanguageError,
    parse_source,
)


def test_python_structure_is_extracted():
    source = """
import os
from flask import Flask

class UserService:
    def get_user(self, user_id):
        print(user_id)
        return user_id

def create_app():
    app = Flask(__name__)
    return app
""".strip()

    result = parse_source(
        source,
        "Python",
    )

    assert result["syntax"]["valid"] is True

    function_names = {
        item["name"]
        for item in result["functions"]
    }

    class_names = {
        item["name"]
        for item in result["classes"]
    }

    call_targets = {
        item["target"]
        for item in result["calls"]
    }

    assert "get_user" in function_names
    assert "create_app" in function_names
    assert "UserService" in class_names

    assert len(result["imports"]) == 2
    assert [item["module"] for item in result["imports"]] == [
        "os",
        "flask",
    ]

    assert "print" in call_targets
    assert "Flask" in call_targets


def test_javascript_structure_is_extracted():
    source = """
import api from "./api.js";

const sanitize = (value) => {
    return value.trim();
};

function login(email) {
    return api.login(email);
}

class AuthService {
    validate(token) {
        console.log(token);
        return true;
    }
}
""".strip()

    result = parse_source(
        source,
        "JavaScript",
    )

    assert result["syntax"]["valid"] is True

    functions = {
        item["name"]: item
        for item in result["functions"]
    }

    classes = {
        item["name"]
        for item in result["classes"]
    }

    calls = {
        item["target"]
        for item in result["calls"]
    }

    assert "sanitize" in functions
    assert "login" in functions
    assert "validate" in functions

    assert functions["sanitize"]["kind"] == (
        "arrow_function"
    )

    assert "AuthService" in classes

    assert len(result["imports"]) == 1
    assert result["imports"][0]["module"] == "./api.js"

    assert "api.login" in calls
    assert "console.log" in calls


def test_invalid_python_syntax_is_reported():
    source = """
def broken(
    print("hello")
""".strip()

    result = parse_source(
        source,
        "Python",
    )

    assert result["syntax"]["valid"] is False
    assert result["syntax"]["error_count"] >= 1


def test_unverified_language_parser_is_rejected():
    with pytest.raises(
        UnsupportedParserLanguageError,
        match="No verified parser",
    ):
        parse_source(
            "public class Test {}",
            "Java",
        )


def test_parsing_does_not_execute_source_code(
    tmp_path,
):
    target = tmp_path / "must_not_exist.txt"

    source = (
        "from pathlib import Path\n"
        f"Path({str(target)!r}).write_text("
        "'dangerous side effect'"
        ")\n"
    )

    result = parse_source(
        source,
        "Python",
    )

    assert result["syntax"]["valid"] is True
    assert target.exists() is False


def test_python_assignment_is_extracted():
    source = '''
def get_user():
    user_id = request.args.get("id")
    return user_id
'''.strip()

    result = parse_source(source, "Python")

    assert result["assignments"] == [
        {
            "target": "user_id",
            "value": 'request.args.get("id")',
            "kind": "assignment",
            "target_location": {
                "start_line": 2,
                "end_line": 2,
                "start_column": 4,
                "end_column": 11,
            },
            "value_location": {
                "start_line": 2,
                "end_line": 2,
                "start_column": 14,
                "end_column": 36,
            },
            "start_line": 2,
            "end_line": 2,
            "start_column": 4,
            "end_column": 36,
        }
    ]


def test_python_call_arguments_are_extracted():
    result = parse_source(
        "def login(user_id):\n    return get_user(user_id)\n",
        "Python",
    )

    call = next(
        item
        for item in result["calls"]
        if item["target"] == "get_user"
    )

    assert call["arguments"] == "(user_id)"
    assert [
        item["text"] for item in call["argument_values"]
    ] == ["user_id"]


def test_javascript_variable_assignment_is_extracted():
    result = parse_source(
        "function login(req) {\n"
        "    const userId = req.query.id;\n"
        "    return userId;\n"
        "}\n",
        "JavaScript",
    )

    assignment = result["assignments"][0]
    assert assignment["target"] == "userId"
    assert assignment["value"] == "req.query.id"
    assert assignment["kind"] == "variable_declaration"


def test_javascript_reassignment_is_extracted():
    result = parse_source(
        "function normalize(value) {\n"
        "    let clean = value;\n"
        "    clean = clean.trim();\n"
        "    return clean;\n"
        "}\n",
        "JavaScript",
    )

    values = {
        (item["target"], item["value"])
        for item in result["assignments"]
    }
    assert ("clean", "value") in values
    assert ("clean", "clean.trim()") in values


def test_javascript_call_arguments_are_extracted():
    result = parse_source(
        "function login(userId) {\n"
        "    return api.login(userId);\n"
        "}\n",
        "JavaScript",
    )

    call = next(
        item
        for item in result["calls"]
        if item["target"] == "api.login"
    )
    assert call["arguments"] == "(userId)"
    assert [
        item["text"] for item in call["argument_values"]
    ] == ["userId"]


def test_python_branch_regions_are_extracted():
    result = parse_source(
        "def choose(first, second):\n"
        "    if first:\n"
        "        value = 1\n"
        "    elif second:\n"
        "        value = 2\n"
        "    else:\n"
        "        value = 3\n",
        "Python",
    )

    regions = result["control_regions"]
    assert [region["kind"] for region in regions] == [
        "IF",
        "ELIF",
        "ELSE",
    ]
    assert len({region["group_id"] for region in regions}) == 1
    assert [region["condition"] for region in regions] == [
        "first",
        "second",
        None,
    ]


def test_javascript_branch_regions_are_extracted():
    result = parse_source(
        "function choose(value) {\n"
        "  if (value) { return 1; }\n"
        "  else { return 2; }\n"
        "}\n",
        "JavaScript",
    )

    assert [
        region["kind"]
        for region in result["control_regions"]
    ] == ["IF", "ELSE"]


def test_parameters_and_returns_are_structured():
    result = parse_source(
        "def normalize(value, fallback=None):\n"
        "    return value or fallback\n",
        "Python",
    )

    function = result["functions"][0]
    assert [
        item["text"]
        for item in function["parameter_values"]
    ] == ["value", "fallback=None"]
    assert result["returns"][0]["value"] == "value or fallback"


def test_javascript_return_is_structured():
    result = parse_source(
        "function normalize(value) { return value.trim(); }",
        "JavaScript",
    )

    assert result["returns"][0]["value"] == "value.trim()"


def test_python_decorators_are_structured_without_regex():
    result = parse_source(
        "@app.get('/users/<int:user_id>')\n"
        "@login_required\n"
        "def get_user(user_id):\n"
        "    return service.load(user_id)\n",
        "Python",
    )

    assert [
        decorator["target"]
        for decorator in result["decorators"]
    ] == ["app.get", "login_required"]
    assert result["decorators"][0]["argument_values"][0][
        "text"
    ] == "'/users/<int:user_id>'"
    assert result["decorators"][1]["arguments"] is None
