"""Declared pack coverage, including unsupported competition scenarios."""

from __future__ import annotations


PACK_COVERAGE = (
    ("SQL_INJECTION", "PARTIAL_STATIC_CANDIDATES"),
    ("COMMAND_INJECTION", "PARTIAL_STATIC_CANDIDATES"),
    ("PATH_TRAVERSAL", "NOT_IMPLEMENTED"),
    ("XSS", "NOT_IMPLEMENTED"),
    ("BROKEN_AUTHORIZATION_IDOR", "NOT_IMPLEMENTED"),
)


def pack_coverage() -> list[dict[str, str]]:
    return [{"id": pack_id, "status": status} for pack_id, status in PACK_COVERAGE]
