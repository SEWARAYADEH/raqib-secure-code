from app.dependency_advisories import check_dependency_advisories


DECLARATIONS = [
    {
        "manifest": "requirements.txt",
        "ecosystem": "PyPI",
        "name": "Flask",
        "version": "3.1.3",
        "version_status": "EXACT",
    },
    {
        "manifest": "package.json",
        "ecosystem": "npm",
        "name": "react",
        "version": None,
        "version_status": "UNRESOLVED_RANGE",
    },
]


def test_exact_declaration_uses_fixed_osv_contract_only():
    payloads = []

    def sender(payload):
        payloads.append(payload)
        return {"results": [{"vulns": [{"id": "GHSA-1234-abcd-5678"}]}]}

    result = check_dependency_advisories(
        DECLARATIONS, enabled=True, transport=sender
    )

    assert payloads == [{"queries": [{
        "package": {"ecosystem": "PyPI", "name": "Flask"},
        "version": "3.1.3",
    }]}]
    assert result["status"] == "PARTIAL"
    assert result["counts"] == {
        "exact_versions_queried": 1,
        "declarations_skipped": 1,
        "advisory_matches": 1,
    }
    assert result["advisory_matches"][0]["status"] == (
        "ADVISORY_MATCH_UNVERIFIED_REACHABILITY"
    )
    assert result["claims"]["vulnerability_verified"] is False


def test_failed_or_truncated_provider_fails_closed():
    for response in (
        {"results": []},
        {"results": [{"vulns": [{"id": "invalid id"}]}]},
    ):
        result = check_dependency_advisories(
            DECLARATIONS[:1], enabled=True,
            transport=lambda _: response,
        )
        assert result["status"] == "UNAVAILABLE"
        assert result["advisory_matches"] == []


def test_disabled_lookup_does_not_call_provider():
    result = check_dependency_advisories(
        DECLARATIONS,
        transport=lambda _: (_ for _ in ()).throw(AssertionError("called")),
    )
    assert result["status"] == "DISABLED"
