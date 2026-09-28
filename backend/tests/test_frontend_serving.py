from app import create_app


def _app(tmp_path):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><title>Raqeeb</title><div id='root'>ready</div>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text(
        "window.__RAQEEB__ = true;",
        encoding="utf-8",
    )
    return create_app(
        {
            "TESTING": True,
            "EMAIL_VERIFICATION_ENABLED": False,
            "ANALYSIS_LOCAL_ONLY": True,
            "FRONTEND_DIST_PATH": str(dist),
        }
    )


def test_production_frontend_index_is_served(tmp_path):
    response = _app(tmp_path).test_client().get("/")

    assert response.status_code == 200
    assert "Raqeeb" in response.get_data(as_text=True)


def test_spa_route_falls_back_to_index(tmp_path):
    response = _app(tmp_path).test_client().get("/analyses/example")

    assert response.status_code == 200
    assert "id='root'" in response.get_data(as_text=True)


def test_frontend_asset_is_served_without_spa_fallback(tmp_path):
    response = _app(tmp_path).test_client().get("/assets/app.js")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "window.__RAQEEB__ = true;"


def test_unknown_api_path_is_never_rewritten_to_frontend(tmp_path):
    response = _app(tmp_path).test_client().get("/api/not-a-real-endpoint")

    assert response.status_code == 404
    assert "Raqeeb" not in response.get_data(as_text=True)
