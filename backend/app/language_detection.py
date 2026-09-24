from __future__ import annotations

from tree_sitter import Parser

from app.parser_engine import JAVASCRIPT_LANGUAGE, PYTHON_LANGUAGE


STATUS_HINT_ONLY = "HINT_ONLY"
STATUS_CORROBORATED = "CORROBORATED"
STATUS_CONFLICT = "CONFLICT"
STATUS_UNKNOWN = "UNKNOWN"


def detect_language(
    language_hint: str | None,
    source_text: str,
) -> dict:
    shebang_hint = _detect_shebang_language(source_text)
    syntax = _syntax_evidence(source_text)
    syntax_hint = syntax["distinctive_language"]

    def result(candidate: str | None, status: str) -> dict:
        output = _build_result(
            candidate=candidate,
            status=status,
            extension_hint=language_hint,
            shebang_hint=shebang_hint,
        )
        output["syntax_evidence"] = syntax
        if syntax_hint:
            output["evidence"].append(
                {"source": "syntax_tree", "language": syntax_hint}
            )
        return output

    if language_hint and shebang_hint:
        if language_hint != shebang_hint:
            return result(None, STATUS_CONFLICT)

    asserted = shebang_hint or language_hint
    if asserted:
        family = _family(asserted)
        if syntax_hint and _family(syntax_hint) != family:
            return result(None, STATUS_CONFLICT)
        corroborated = (
            bool(language_hint and shebang_hint)
            or bool(syntax_hint and _family(syntax_hint) == family)
        )
        return result(
            asserted,
            STATUS_CORROBORATED if corroborated else STATUS_HINT_ONLY,
        )

    if syntax_hint:
        return result(syntax_hint, STATUS_CORROBORATED)
    return result(None, STATUS_UNKNOWN)


def _family(language: str) -> str | None:
    if language == "Python":
        return "Python"
    if language in {"JavaScript", "JavaScript JSX"}:
        return "JavaScript"
    return None


def _syntax_evidence(source_text: str) -> dict:
    source = source_text.encode("utf-8")
    valid = {}
    distinctive = {}
    node_types = {
        "Python": {
            "function_definition", "class_definition", "import_from_statement",
            "decorated_definition", "with_statement", "async_function_definition",
        },
        "JavaScript": {
            "function_declaration", "arrow_function", "lexical_declaration",
            "export_statement", "jsx_element", "jsx_self_closing_element",
        },
    }
    for language, grammar in (
        ("Python", PYTHON_LANGUAGE),
        ("JavaScript", JAVASCRIPT_LANGUAGE),
    ):
        root = Parser(grammar).parse(source).root_node
        valid[language] = not root.has_error
        pending = [root]
        found = False
        while pending:
            node = pending.pop()
            if node.type in node_types[language]:
                found = True
                break
            pending.extend(node.named_children)
        distinctive[language] = found and valid[language]

    candidates = [
        name for name in valid
        if valid[name] and distinctive[name]
    ]
    return {
        "valid": valid,
        "distinctive_language": candidates[0] if len(candidates) == 1 else None,
    }


def _detect_shebang_language(
    source_text: str,
) -> str | None:
    if not source_text:
        return None

    first_line = source_text.splitlines()[0].strip()

    if not first_line.startswith("#!"):
        return None

    shebang = first_line.lower()

    rules = (
        (("python",), "Python"),
        (("node", "nodejs"), "JavaScript"),
        (("php",), "PHP"),
        (("ruby",), "Ruby"),
        (("pwsh", "powershell"), "PowerShell"),
        (
            (
                "/bash",
                "/sh",
                "/zsh",
                "env bash",
                "env sh",
                "env zsh",
            ),
            "Shell",
        ),
    )

    for indicators, language in rules:
        if any(
            indicator in shebang
            for indicator in indicators
        ):
            return language

    return None


def _build_result(
    *,
    candidate: str | None,
    status: str,
    extension_hint: str | None,
    shebang_hint: str | None,
) -> dict:
    evidence = []

    if extension_hint:
        evidence.append(
            {
                "source": "extension",
                "language": extension_hint,
            }
        )

    if shebang_hint:
        evidence.append(
            {
                "source": "shebang",
                "language": shebang_hint,
            }
        )

    return {
        "candidate": candidate,
        "status": status,
        "extension_hint": extension_hint,
        "shebang_hint": shebang_hint,
        "evidence": evidence,
    }
