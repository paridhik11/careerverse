"""Tests for POST /auth/google.

Google's own token verification calls out to Google's servers, so we mock
`app.services.auth_service.verify_google_id_token` (the only seam between our
code and Google) rather than hitting the network in tests.
"""

from app.core.security import GoogleTokenError

VALID_PASSWORD = "supersecret1"


def _fake_claims(email: str, google_id: str = "google-sub-123") -> dict:
    return {"sub": google_id, "email": email, "email_verified": True}


def test_google_auth_creates_new_user(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token",
        lambda credential: _fake_claims("google.new@example.com"),
    )

    response = client.post("/auth/google", json={"credential": "fake-id-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "google.new@example.com"


def test_google_auth_links_existing_password_account_by_email(client, monkeypatch) -> None:
    signup_payload = {"email": "shared@example.com", "password": VALID_PASSWORD}
    signup_response = client.post("/signup", json=signup_payload)
    existing_user_id = signup_response.json()["user"]["id"]

    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token",
        lambda credential: _fake_claims("shared@example.com", google_id="google-sub-456"),
    )

    response = client.post("/auth/google", json={"credential": "fake-id-token"})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == existing_user_id


def test_google_auth_reuses_same_account_on_repeat_login(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token",
        lambda credential: _fake_claims("repeat@example.com", google_id="google-sub-789"),
    )

    first = client.post("/auth/google", json={"credential": "fake-id-token"})
    second = client.post("/auth/google", json={"credential": "fake-id-token"})

    assert first.json()["user"]["id"] == second.json()["user"]["id"]


def test_google_auth_invalid_token_returns_401(client, monkeypatch) -> None:
    def _raise(_credential: str) -> dict:
        raise GoogleTokenError("Invalid or expired Google credential.")

    monkeypatch.setattr("app.services.auth_service.verify_google_id_token", _raise)

    response = client.post("/auth/google", json={"credential": "not-a-real-token"})

    assert response.status_code == 401
