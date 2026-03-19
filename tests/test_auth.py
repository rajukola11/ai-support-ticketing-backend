import pytest


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "NewPass@1234"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "Dup@1234"
        })
        response = client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "Dup@1234"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password_too_short(self, client):
        response = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "abc"
        })
        assert response.status_code == 422

    def test_register_weak_password_no_uppercase(self, client):
        response = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "nouppercase1!"
        })
        assert response.status_code == 422

    def test_register_weak_password_no_number(self, client):
        response = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "NoNumber!"
        })
        assert response.status_code == 422

    def test_register_weak_password_no_special_char(self, client):
        response = client.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "NoSpecial1"
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        response = client.post("/auth/register", json={
            "email": "notanemail",
            "password": "Valid@1234"
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post("/auth/register", json={
            "email": "login@example.com",
            "password": "Login@1234"
        })
        response = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "Login@1234"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "email": "loginwrong@example.com",
            "password": "Correct@1234"
        })
        response = client.post("/auth/login", json={
            "email": "loginwrong@example.com",
            "password": "Wrong@1234"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "email": "ghost@example.com",
            "password": "Ghost@1234"
        })
        assert response.status_code == 401


class TestRefreshToken:
    def test_refresh_success(self, client):
        client.post("/auth/register", json={
            "email": "refresh@example.com",
            "password": "Refresh@1234"
        })
        login = client.post("/auth/login", json={
            "email": "refresh@example.com",
            "password": "Refresh@1234"
        })
        refresh_token = login.json()["refresh_token"]

        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different (rotation)
        assert data["refresh_token"] != refresh_token

    def test_refresh_reuse_old_token_fails(self, client):
        client.post("/auth/register", json={
            "email": "rotate@example.com",
            "password": "Rotate@1234"
        })
        login = client.post("/auth/login", json={
            "email": "rotate@example.com",
            "password": "Rotate@1234"
        })
        old_token = login.json()["refresh_token"]
        client.post("/auth/refresh", json={"refresh_token": old_token})

        # Try to use old token again
        response = client.post("/auth/refresh", json={"refresh_token": old_token})
        assert response.status_code == 401

    def test_refresh_invalid_token(self, client):
        response = client.post("/auth/refresh", json={"refresh_token": "invalidtoken"})
        assert response.status_code == 401


class TestLogout:
    def test_logout_success(self, client):
        client.post("/auth/register", json={
            "email": "logout@example.com",
            "password": "Logout@1234"
        })
        login = client.post("/auth/login", json={
            "email": "logout@example.com",
            "password": "Logout@1234"
        })
        refresh_token = login.json()["refresh_token"]

        response = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert response.status_code == 204

    def test_refresh_after_logout_fails(self, client):
        client.post("/auth/register", json={
            "email": "logoutrefresh@example.com",
            "password": "Logout@1234"
        })
        login = client.post("/auth/login", json={
            "email": "logoutrefresh@example.com",
            "password": "Logout@1234"
        })
        refresh_token = login.json()["refresh_token"]
        client.post("/auth/logout", json={"refresh_token": refresh_token})

        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401


class TestMe:
    def test_get_me_success(self, client, auth_headers):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"

    def test_get_me_no_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert response.status_code == 401