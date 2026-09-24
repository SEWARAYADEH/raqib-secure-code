from app.language_detection import (
    STATUS_CONFLICT,
    STATUS_CORROBORATED,
    STATUS_HINT_ONLY,
    STATUS_UNKNOWN,
    detect_language,
)


def test_extension_only_is_hint():
    result = detect_language(
        "Python",
        "print('hello')\n",
    )

    assert result["candidate"] == "Python"
    assert result["status"] == STATUS_HINT_ONLY
    assert result["extension_hint"] == "Python"
    assert result["shebang_hint"] is None


def test_python_extension_and_shebang_are_corroborated():
    result = detect_language(
        "Python",
        "#!/usr/bin/env python3\nprint('hello')\n",
    )

    assert result["candidate"] == "Python"
    assert result["status"] == STATUS_CORROBORATED
    assert result["shebang_hint"] == "Python"


def test_conflicting_language_evidence_is_not_guessed():
    result = detect_language(
        "JavaScript",
        "#!/usr/bin/env python3\nprint('hello')\n",
    )

    assert result["candidate"] is None
    assert result["status"] == STATUS_CONFLICT
    assert result["extension_hint"] == "JavaScript"
    assert result["shebang_hint"] == "Python"


def test_shebang_can_classify_file_without_extension_hint():
    result = detect_language(
        None,
        "#!/usr/bin/env python3\nprint('hello')\n",
    )

    assert result["candidate"] == "Python"
    assert result["status"] == STATUS_HINT_ONLY
    assert result["extension_hint"] is None
    assert result["shebang_hint"] == "Python"


def test_unknown_language_remains_unknown():
    result = detect_language(
        None,
        "some unknown text\n",
    )

    assert result["candidate"] is None
    assert result["status"] == STATUS_UNKNOWN
    assert result["evidence"] == []


def test_php_evidence_is_corroborated():
    result = detect_language(
        "PHP",
        "#!/usr/bin/php\n<?php echo 'ok';\n",
    )

    assert result["candidate"] == "PHP"
    assert result["status"] == STATUS_CORROBORATED


def test_shell_shebang_is_detected():
    result = detect_language(
        "Shell",
        "#!/bin/bash\necho hello\n",
    )

    assert result["candidate"] == "Shell"
    assert result["status"] == STATUS_CORROBORATED


def test_syntax_can_identify_extensionless_python_and_javascript():
    python = detect_language(None, "def run():\n    return 1\n")
    javascript = detect_language(None, "function run() { return 1; }\n")

    assert python["candidate"] == "Python"
    assert python["status"] == STATUS_CORROBORATED
    assert javascript["candidate"] == "JavaScript"
    assert javascript["status"] == STATUS_CORROBORATED


def test_distinctive_syntax_disagrees_with_extension_without_guessing():
    result = detect_language(
        "JavaScript", "def run():\n    return 1\n"
    )

    assert result["candidate"] is None
    assert result["status"] == STATUS_CONFLICT
    assert result["syntax_evidence"]["distinctive_language"] == "Python"


def test_ambiguous_syntax_does_not_become_content_language_claim():
    result = detect_language(None, "x = 1\n")

    assert result["candidate"] is None
    assert result["status"] == STATUS_UNKNOWN
