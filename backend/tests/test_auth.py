from __future__ import annotations

import httpx
import pytest

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "securepassword123"
TEST_DISPLAY_NAME = "Test User"


class TestRegister:
    @pytest.mark.asyncio
    async def test_creates_user_and_returns_tokens(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            REGISTER_URL,
            json={
                "email": "newuser@example.com",
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert data["access_token"].count(".") == 2
        assert data["refresh_token"].count(".") == 2

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(
        self, client: httpx.AsyncClient
    ) -> None:
        payload = {
            "email": "duplicate@example.com",
            "password": TEST_PASSWORD,
            "display_name": TEST_DISPLAY_NAME,
        }
        await client.post(REGISTER_URL, json=payload)
        response = await client.post(REGISTER_URL, json=payload)
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_minimal_valid_data_returns_201(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            REGISTER_URL,
            json={
                "email": "minimal@example.com",
                "password": "a" * 8,
                "display_name": "M",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


class TestLogin:
    @pytest.mark.asyncio
    async def test_correct_credentials_returns_tokens(
        self, client: httpx.AsyncClient
    ) -> None:
        email = "login-ok@example.com"
        await client.post(
            REGISTER_URL,
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        response = await client.post(
            LOGIN_URL,
            json={"email": email, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(
        self, client: httpx.AsyncClient
    ) -> None:
        email = "wrong-pw@example.com"
        await client.post(
            REGISTER_URL,
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        response = await client.post(
            LOGIN_URL,
            json={"email": email, "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_nonexistent_email_returns_401(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            LOGIN_URL,
            json={
                "email": "nonexistent@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"


class TestRefresh:
    @pytest.mark.asyncio
    async def test_valid_refresh_token_returns_new_tokens(
        self, client: httpx.AsyncClient
    ) -> None:
        reg = await client.post(
            REGISTER_URL,
            json={
                "email": "refresh-valid@example.com",
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        original = reg.json()
        refresh_token = original["refresh_token"]

        response = await client.post(
            REFRESH_URL, json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["access_token"] != original["access_token"]
        assert data["refresh_token"] != original["refresh_token"]

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            REFRESH_URL, json={"refresh_token": "not-a-valid-jwt"}
        )
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_access_token_rejected_with_401(
        self, client: httpx.AsyncClient
    ) -> None:
        reg = await client.post(
            REGISTER_URL,
            json={
                "email": "access-as-refresh@example.com",
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        access_token = reg.json()["access_token"]
        response = await client.post(
            REFRESH_URL, json={"refresh_token": access_token}
        )
        assert response.status_code == 401
        assert "Invalid token type" in response.json()["detail"]


class TestLogout:
    @pytest.mark.asyncio
    async def test_valid_token_returns_204(
        self, client: httpx.AsyncClient
    ) -> None:
        reg = await client.post(
            REGISTER_URL,
            json={
                "email": "logout-test@example.com",
                "password": TEST_PASSWORD,
                "display_name": TEST_DISPLAY_NAME,
            },
        )
        refresh_token = reg.json()["refresh_token"]
        response = await client.post(
            LOGOUT_URL, json={"refresh_token": refresh_token}
        )
        assert response.status_code == 204
        assert response.content == b""
