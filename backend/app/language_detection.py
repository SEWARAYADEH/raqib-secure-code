from __future__ import annotations


STATUS_HINT_ONLY = "HINT_ONLY"
STATUS_CORROBORATED = "CORROBORATED"
STATUS_CONFLICT = "CONFLICT"
STATUS_UNKNOWN = "UNKNOWN"


def detect_language(
    language_hint: str | None,
    source_text: str,
) -> dict:
    shebang_hint = _detect_shebang_language(source_text)

    if language_hint and shebang_hint:
        if language_hint == shebang_hint:
            return _build_result(
                candidate=language_hint,
                status=STATUS_CORROBORATED,
                extension_hint=language_hint,
                shebang_hint=shebang_hint,
            )

        return _build_result(
            candidate=None,
            status=STATUS_CONFLICT,
            extension_hint=language_hint,
            shebang_hint=shebang_hint,
        )

    if language_hint:
        return _build_result(
            candidate=language_hint,
            status=STATUS_HINT_ONLY,
            extension_hint=language_hint,
            shebang_hint=None,
        )

    if shebang_hint:
        return _build_result(
            candidate=shebang_hint,
            status=STATUS_HINT_ONLY,
            extension_hint=None,
            shebang_hint=shebang_hint,
        )

    return _build_result(
        candidate=None,
        status=STATUS_UNKNOWN,
        extension_hint=None,
        shebang_hint=None,
    )


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