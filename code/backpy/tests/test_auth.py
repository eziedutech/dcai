import jwt

from app.auth.security import issue_access_token
from tests.conftest import TEST_SECRET, auth, register


def test_register_returns_tokens_and_hashes_password(api, db_url):
    tokens = register(api)

    assert tokens["guardian"]["email"] == "ibu@example.com"
    assert api.get("/v1/auth/me", headers=auth(tokens)).json()["name"] == "Ibu Sari"

    from sqlalchemy import create_engine, text

    with create_engine(db_url).connect() as conn:
        stored = conn.execute(text("SELECT password_hash FROM guardian")).scalar_one()
        refresh = conn.execute(text("SELECT token_hash FROM refresh_token")).scalar_one()
    assert stored.startswith("$argon2")
    assert "kata-sandi-panjang" not in stored
    assert refresh != tokens["refresh_token"]


def test_duplicate_email_is_conflict_case_insensitive(api):
    register(api)
    resp = api.post(
        "/v1/auth/register",
        json={"email": "IBU@example.com", "password": "kata-sandi-panjang", "name": "X"},
    )
    assert resp.status_code == 409


def test_short_password_rejected(api):
    resp = api.post(
        "/v1/auth/register", json={"email": "a@example.com", "password": "pendek", "name": "A"}
    )
    assert resp.status_code == 422


def test_login(api):
    register(api)
    ok = api.post(
        "/v1/auth/login", json={"email": "ibu@example.com", "password": "kata-sandi-panjang"}
    )
    wrong = api.post("/v1/auth/login", json={"email": "ibu@example.com", "password": "salah"})
    unknown = api.post(
        "/v1/auth/login", json={"email": "siapa@example.com", "password": "kata-sandi-panjang"}
    )

    assert ok.status_code == 200
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json() == unknown.json()  # no hint whether the email exists


def test_protected_route_needs_valid_token(api):
    tokens = register(api)
    guardian_id = tokens["guardian"]["id"]
    import uuid

    expired, _ = issue_access_token(uuid.UUID(guardian_id), TEST_SECRET, minutes=-1)
    forged, _ = issue_access_token(uuid.UUID(guardian_id), "another-secret-" * 4, minutes=5)
    wrong_type = jwt.encode(
        {"sub": guardian_id, "typ": "refresh", "exp": 9999999999}, TEST_SECRET, algorithm="HS256"
    )

    assert api.get("/v1/children").status_code == 401
    for token in (expired, forged, wrong_type, "not-a-jwt"):
        resp = api.get("/v1/children", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401, token


def test_access_token_is_short_lived(api):
    tokens = register(api)
    claims = jwt.decode(tokens["access_token"], TEST_SECRET, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_refresh_rotates_and_reuse_ends_all_sessions(api):
    first = register(api)

    second = api.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    second = second.json()
    assert second["refresh_token"] != first["refresh_token"]

    # Replaying the used token is treated as theft: it fails and revokes the live one too.
    replay = api.post("/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    after = api.post("/v1/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert replay.status_code == 401
    assert after.status_code == 401


def test_logout_revokes_refresh_token(api):
    tokens = register(api)
    resp = api.post(
        "/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=auth(tokens)
    )
    assert resp.status_code == 204
    again = api.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert again.status_code == 401


def test_change_password(api):
    tokens = register(api)
    # Wrong current password is refused.
    bad = api.post(
        "/v1/auth/change-password",
        json={"current_password": "salah", "new_password": "sandi-baru-panjang"},
        headers=auth(tokens),
    )
    assert bad.status_code == 401
    ok = api.post(
        "/v1/auth/change-password",
        json={"current_password": "kata-sandi-panjang", "new_password": "sandi-baru-panjang"},
        headers=auth(tokens),
    )
    assert ok.status_code == 204
    # The new password works; the old one no longer does.
    assert (
        api.post(
            "/v1/auth/login", json={"email": "ibu@example.com", "password": "sandi-baru-panjang"}
        ).status_code
        == 200
    )
    assert (
        api.post(
            "/v1/auth/login", json={"email": "ibu@example.com", "password": "kata-sandi-panjang"}
        ).status_code
        == 401
    )


def test_logout_all_ends_every_session(api):
    tokens = register(api)
    second = api.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).json()
    resp = api.post("/v1/auth/logout-all", headers=auth(second))
    assert resp.status_code == 204
    # The newest refresh token no longer works either.
    assert (
        api.post("/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code
        == 401
    )


def test_no_secret_key_refuses_to_issue_tokens(api, monkeypatch):
    api.app.state.settings.secret_key = ""
    resp = api.post(
        "/v1/auth/register",
        json={"email": "b@example.com", "password": "kata-sandi-panjang", "name": "B"},
    )
    assert resp.status_code == 503
