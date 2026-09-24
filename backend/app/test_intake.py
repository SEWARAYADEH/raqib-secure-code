import hashlib

import pytest

from app.intake import (
    SourceFileValidationError,
    inspect_source_file,
)


def test_python_source_profile():
    content = (
        b"def hello(name):\n"
        b"    return f'Hello {name}'\n"
    )

    result = inspect_source_file(
        "example.py",
        content,
    )

    assert result["filename"] == "example.py"
    assert result["extension"] == ".py"
    assert result["language_hint"] == "Python"
    assert result["line_count"] == 2
    assert result["size_bytes"] == len(content)
    assert result["encoding"] == "UTF-8"
    assert result["sha256"] == hashlib.sha256(
        content
    ).hexdigest()


def test_javascript_source_profile():
    content = (
        b"function login() {\n"
        b"  return true;\n"
        b"}\n"
    )

    result = inspect_source_file(
        "auth.js",
        content,
    )

    assert result["language_hint"] == "JavaScript"
    assert result["line_count"] == 3


def test_typescript_tsx_detection():
    content = (
        b"export function App() {\n"
        b"  return null;\n"
        b"}\n"
    )

    result = inspect_source_file(
        "component.tsx",
        content,
    )

    assert result["language_hint"] == "TypeScript TSX"


def test_multiple_dot_filename_is_preserved():
    content = b"<?php echo 'ok';\n"

    result = inspect_source_file(
        "security.config.php",
        content,
    )

    assert result["filename"] == "security.config.php"
    assert result["extension"] == ".php"
    assert result["language_hint"] == "PHP"


def test_empty_file_is_rejected():
    with pytest.raises(
        SourceFileValidationError,
        match="empty",
    ):
        inspect_source_file(
            "empty.py",
            b"",
        )


def test_binary_file_is_rejected():
    content = b"abc\x00def"

    with pytest.raises(
        SourceFileValidationError,
        match="Binary",
    ):
        inspect_source_file(
            "payload.py",
            content,
        )


def test_path_traversal_filename_is_rejected():
    with pytest.raises(
        SourceFileValidationError,
        match="path",
    ):
        inspect_source_file(
            "../secret.py",
            b"print('test')\n",
        )


def test_windows_path_filename_is_rejected():
    with pytest.raises(
        SourceFileValidationError,
        match="path",
    ):
        inspect_source_file(
            "..\\secret.py",
            b"print('test')\n",
        )


def test_unknown_extension_remains_unclassified():
    content = b"some readable source text\n"

    result = inspect_source_file(
        "unknown.custom",
        content,
    )

    assert result["extension"] == ".custom"
    assert result["language_hint"] is None
