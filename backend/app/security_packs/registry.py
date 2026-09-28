"""Focused competition security-pack registry.

Coverage metadata is intentionally explicit. A pack can be visible in the
product before runtime verification, patching, or closure are implemented;
those capabilities must remain false until evidence-backed gates exist.
"""

from __future__ import annotations


PACKS = (
    {
        "id": "SQL_INJECTION",
        "display_name": "SQL Injection",
        "implementation_order": 1,
        "status": "PARTIAL_STATIC_CANDIDATES",
        "understanding_focus": "HTTP input -> query construction -> SQL execution -> parameter binding",
        "can_verify_exploitability": False,
        "can_generate_verified_patch": False,
        "can_close": False,
    },
    {
        "id": "COMMAND_INJECTION",
        "display_name": "Command Injection",
        "implementation_order": 2,
        "status": "PARTIAL_STATIC_CANDIDATES",
        "understanding_focus": "Input -> command construction -> process/shell sink -> execution controls",
        "can_verify_exploitability": False,
        "can_generate_verified_patch": False,
        "can_close": False,
    },
    {
        "id": "PATH_TRAVERSAL",
        "display_name": "Path Traversal",
        "implementation_order": 3,
        "status": "NOT_IMPLEMENTED",
        "understanding_focus": "Input path -> normalization/join -> filesystem operation -> allowed root",
        "can_verify_exploitability": False,
        "can_generate_verified_patch": False,
        "can_close": False,
    },
    {
        "id": "XSS",
        "display_name": "Cross-Site Scripting",
        "implementation_order": 4,
        "status": "NOT_IMPLEMENTED",
        "understanding_focus": "Input -> transformations -> HTML/JavaScript sink -> context encoding",
        "can_verify_exploitability": False,
        "can_generate_verified_patch": False,
        "can_close": False,
    },
    {
        "id": "BROKEN_AUTHORIZATION_IDOR",
        "display_name": "Broken Authorization / IDOR",
        "implementation_order": 5,
        "status": "NOT_IMPLEMENTED",
        "understanding_focus": "Route -> actor -> resource ID -> ownership/role guard -> resource access",
        "can_verify_exploitability": False,
        "can_generate_verified_patch": False,
        "can_close": False,
    },
)


def pack_coverage() -> list[dict]:
    return [dict(pack) for pack in PACKS]
