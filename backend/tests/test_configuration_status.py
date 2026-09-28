from app import create_app


def test_configuration_status_exposes_flags_without_secret_values():
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": True,
        "OPENAI_API_KEY": "unit-test-secret-do-not-return",
        "OPENAI_MODEL": "test-model",
        "CODEX_ADVISOR_ENABLED": True,
        "OSV_ADVISORY_LOOKUP_ENABLED": True,
        "EMAIL_VERIFICATION_ENABLED": False,
    })
    response = app.test_client().get("/api/v1/configuration/status")
    assert response.status_code == 200
    assert response.json["ai"]["key_configured"] is True
    assert response.json["ai"]["model"] == "test-model"
    assert response.json["analysis"]["uploaded_code_execution"] is False
    assert response.json["analysis"]["osv_advisory_lookup_enabled"] is True
    assert response.json["storage"]["analysis_records"] == "OWNER_SCOPED_APPEND_ONLY"
    assert response.json["storage"]["uploaded_source_retention"] == "TEMPORARY_WORKSPACE_ONLY"
    assert response.json["storage"]["original_overwritten"] is False
    assert "unit-test-secret-do-not-return" not in response.get_data(as_text=True)


def test_configuration_status_requires_principal():
    app = create_app({
        "TESTING": True,
        "ANALYSIS_LOCAL_ONLY": False,
        "EMAIL_VERIFICATION_ENABLED": False,
    })
    response = app.test_client().get("/api/v1/configuration/status")
    assert response.status_code == 401
