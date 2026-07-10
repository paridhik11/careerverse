"""Tests for POST /signup, POST /login, and GET /me."""

VALID_PASSWORD = "supersecret1"


def test_signup_success(client) -> None:
    response = client.post(
        "/signup", json={"email": "new.user@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "new.user@example.com"
    assert "password" not in body["user"]


def test_signup_duplicate_email_returns_409(client) -> None:
    payload = {"email": "dup@example.com", "password": VALID_PASSWORD}

    first = client.post("/signup", json=payload)
    assert first.status_code == 201

    second = client.post("/signup", json=payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


def test_signup_password_too_short_returns_422(client) -> None:
    response = client.post(
        "/signup", json={"email": "shortpw@example.com", "password": "short"}
    )

    assert response.status_code == 422


def test_login_success(client) -> None:
    payload = {"email": "login.user@example.com", "password": VALID_PASSWORD}
    client.post("/signup", json=payload)

    response = client.post("/login", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == payload["email"]


def test_login_wrong_password_returns_401(client) -> None:
    payload = {"email": "wrongpass.user@example.com", "password": VALID_PASSWORD}
    client.post("/signup", json=payload)

    response = client.post(
        "/login", json={"email": payload["email"], "password": "incorrect-password"}
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_me_with_valid_token_returns_current_user(client) -> None:
    payload = {"email": "me.user@example.com", "password": VALID_PASSWORD}
    signup_response = client.post("/signup", json=payload)
    token = signup_response.json()["access_token"]

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == payload["email"]


def test_me_with_invalid_token_returns_401(client) -> None:
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_without_token_returns_401(client) -> None:
    response = client.get("/me")

    assert response.status_code == 401
