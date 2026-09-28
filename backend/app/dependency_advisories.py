"""Bounded, opt-in OSV lookup for exact dependency declarations only."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OSV_QUERY_URL = "https://api.osv.dev/v1/querybatch"
MAX_QUERIES = 50
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_ADVISORIES_PER_PACKAGE = 100
_ADVISORY_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,99}$")


def check_dependency_advisories(
    declarations: list[dict], *, enabled: bool = False, transport=None
) -> dict:
    exact = [
        item for item in declarations
        if item.get("version_status") == "EXACT"
        and item.get("ecosystem") in {"PyPI", "npm"}
        and isinstance(item.get("name"), str)
        and isinstance(item.get("version"), str)
    ]
    skipped = len(declarations) - len(exact)
    if not enabled:
        return _result("DISABLED", [], 0, skipped + len(exact))
    if not exact:
        return _result("NO_EXACT_VERSIONS", [], 0, skipped)

    selected = exact[:MAX_QUERIES]
    skipped += len(exact) - len(selected)
    queries = [
        {
            "package": {
                "ecosystem": item["ecosystem"],
                "name": item["name"],
            },
            "version": item["version"],
        }
        for item in selected
    ]
    sender = transport or _post_osv
    try:
        response = sender({"queries": queries})
        results = response["results"]
        if not isinstance(results, list) or len(results) != len(selected):
            raise ValueError("OSV result count mismatch")
        matches = []
        incomplete = skipped > 0
        for declaration, item in zip(selected, results):
            if not isinstance(item, dict) or not isinstance(item.get("vulns", []), list):
                raise ValueError("Invalid OSV result")
            advisories = item.get("vulns", [])
            if item.get("next_page_token") or len(advisories) > MAX_ADVISORIES_PER_PACKAGE:
                incomplete = True
            for advisory in advisories[:MAX_ADVISORIES_PER_PACKAGE]:
                advisory_id = advisory.get("id") if isinstance(advisory, dict) else None
                if not isinstance(advisory_id, str) or not _ADVISORY_ID.fullmatch(advisory_id):
                    raise ValueError("Invalid OSV advisory identifier")
                matches.append(
                    {
                        "manifest": declaration["manifest"],
                        "ecosystem": declaration["ecosystem"],
                        "name": declaration["name"],
                        "version": declaration["version"],
                        "advisory_id": advisory_id,
                        "source": "OSV",
                        "status": "ADVISORY_MATCH_UNVERIFIED_REACHABILITY",
                    }
                )
    except (OSError, ValueError, KeyError, TypeError, HTTPError, URLError):
        return _result("UNAVAILABLE", [], 0, skipped + len(selected))

    return _result(
        "PARTIAL" if incomplete else "COMPLETED",
        matches,
        len(selected),
        skipped,
    )


def _post_osv(payload: dict) -> dict:
    request = Request(
        OSV_QUERY_URL,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=5) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("OSV response exceeds size limit")
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError("Invalid OSV response")
    return document


def _result(status: str, matches: list[dict], queried: int, skipped: int) -> dict:
    return {
        "provider": "OSV",
        "status": status,
        "advisory_matches": matches,
        "counts": {
            "exact_versions_queried": queried,
            "declarations_skipped": skipped,
            "advisory_matches": len(matches),
        },
        "claims": {
            "installed_version_verified": False,
            "runtime_reachability_verified": False,
            "vulnerability_verified": False,
        },
    }
