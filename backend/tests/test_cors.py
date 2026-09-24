from app import create_app


def test_frontend_origin_is_allowed():
    app = create_app()
    app.config.update(TESTING=True)

    client = app.test_client()

    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers.get("Access-Control-Allow-Origin")
        == "http://localhost:5173"
    )


def test_unknown_origin_is_not_allowed():
    app = create_app()
    app.config.update(TESTING=True)

    client = app.test_client()

    response = client.get(
        "/api/health",
        headers={
            "Origin": "http://example.com",
        },
    )

    assert response.status_code == 200

    assert response.headers.get(
        "Access-Control-Allow-Origin"
    ) is None