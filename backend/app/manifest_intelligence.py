"""Read bounded dependency declarations without executing project files."""

from __future__ import annotations

import hashlib
import json
import re


MAX_MANIFEST_BYTES = 256 * 1024
MANIFEST_NAMES = {"package.json", "requirements.txt"}
MAX_DECLARATIONS = 200
_PACKAGE_NAME = re.compile(r"^(?:@[-a-zA-Z0-9._]+/)?[-a-zA-Z0-9._]+$")
_EXACT_VERSION = re.compile(r"^\d+(?:\.\d+){1,3}(?:[-+][a-zA-Z0-9.-]+)?$")
_REQUIREMENT = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*"
    r"(\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?)$"
)


def inspect_manifest(relative_path: str, content: bytes) -> dict:
    result = {
        "relative_path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "status": "PARSED",
        "dependencies": [],
        "unresolved_declarations": 0,
    }
    if len(content) > MAX_MANIFEST_BYTES:
        result["status"] = "TOO_LARGE"
        return result
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        result["status"] = "INVALID_ENCODING"
        return result

    if relative_path.rsplit("/", 1)[-1] == "package.json":
        _read_package_json(result, text)
    else:
        _read_requirements(result, text)
    return result


def _read_package_json(result: dict, text: str) -> None:
    try:
        package = json.loads(text, object_pairs_hook=_unique_object)
    except (ValueError, TypeError, RecursionError):
        result["status"] = "INVALID_MANIFEST"
        return
    if not isinstance(package, dict):
        result["status"] = "INVALID_MANIFEST"
        return
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        declarations = package.get(section, {})
        if not isinstance(declarations, dict):
            result["unresolved_declarations"] += 1
            continue
        for name, version in declarations.items():
            if len(result["dependencies"]) >= MAX_DECLARATIONS:
                result["unresolved_declarations"] += 1
                continue
            if not _PACKAGE_NAME.fullmatch(name) or not isinstance(version, str):
                result["unresolved_declarations"] += 1
                continue
            exact = bool(_EXACT_VERSION.fullmatch(version))
            result["dependencies"].append(
                {
                    "ecosystem": "npm",
                    "name": name,
                    "version": version if exact else None,
                    "version_status": "EXACT" if exact else "UNRESOLVED_RANGE",
                    "scope": section,
                }
            )


def _read_requirements(result: dict, text: str) -> None:
    for line in text.splitlines():
        declaration = line.strip()
        if not declaration or declaration.startswith("#"):
            continue
        match = _REQUIREMENT.fullmatch(declaration)
        if len(result["dependencies"]) >= MAX_DECLARATIONS:
            result["unresolved_declarations"] += 1
            continue
        if match is None:
            result["unresolved_declarations"] += 1
            continue
        result["dependencies"].append(
            {
                "ecosystem": "PyPI",
                "name": match.group(1),
                "version": match.group(2),
                "version_status": "EXACT",
                "scope": "requirements.txt",
            }
        )


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result
