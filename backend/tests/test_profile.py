from __future__ import annotations

import uuid

import httpx
import pytest

REGISTER_URL = "/api/v1/auth/register"
PROFILE_ME_URL = "/api/v1/profile/me"
ONBOARDING_URL = "/api/v1/profile/onboarding"

TEST_PASSWORD = "securepassword123"


@pytest.fixture
async def onboarded_user(client: httpx.AsyncClient) -> dict:
    email = f"onboarded-{uuid.uuid4().hex[:12]}@example.com"
    reg = await client.post(
        REGISTER_URL,
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "display_name": "Test User",
        },
    )
    tokens = reg.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(
        ONBOARDING_URL,
        json={
            "display_name": "Test User",
            "bio": "Hello world",
            "preferences": {"theme": "light"},
        },
        headers=headers,
    )

    return {"headers": headers, **tokens}


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_returns_profile_for_onboarded_user(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        response = await client.get(PROFILE_ME_URL, headers=onboarded_user["headers"])
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Test User"
        assert data["bio"] == "Hello world"
        assert data["preferences"] == {"theme": "light"}
        assert "id" in data
        assert "user_id" in data
        assert "email" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.get(PROFILE_ME_URL)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_403_for_not_onboarded_user(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        email = f"not-onboarded-{uuid.uuid4().hex[:12]}@example.com"
        reg = await client.post(
            REGISTER_URL,
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "display_name": "Not Onboarded",
            },
        )
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        response = await client.get(PROFILE_ME_URL, headers=headers)
        assert response.status_code == 403


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_profile_fields(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        response = await client.patch(
            PROFILE_ME_URL,
            json={"bio": "Updated bio", "location": "New York"},
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio"
        assert data["location"] == "New York"
        assert data["display_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_updates_display_name(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        response = await client.patch(
            PROFILE_ME_URL,
            json={"display_name": "New Name"},
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "New Name"

    @pytest.mark.asyncio
    async def test_partial_update_does_not_clear_existing_fields(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        await client.patch(
            PROFILE_ME_URL,
            json={"bio": "Original bio", "website": "https://example.com"},
            headers=onboarded_user["headers"],
        )
        response = await client.patch(
            PROFILE_ME_URL,
            json={"bio": "Only bio changed"},
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Only bio changed"
        assert data["website"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_empty_update_returns_profile_unchanged(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        response = await client.patch(
            PROFILE_ME_URL,
            json={},
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "Test User"

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.patch(PROFILE_ME_URL, json={"bio": "test"})
        assert response.status_code == 401


class TestPreferences:
    @pytest.mark.asyncio
    async def test_set_preferences_via_update(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        prefs = {"theme": "dark", "language": "en", "notifications": True}
        response = await client.patch(
            PROFILE_ME_URL,
            json={"preferences": prefs},
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["preferences"] == prefs

    @pytest.mark.asyncio
    async def test_preferences_readable_via_get(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        await client.patch(
            PROFILE_ME_URL,
            json={"preferences": {"notifications": False}},
            headers=onboarded_user["headers"],
        )
        response = await client.get(PROFILE_ME_URL, headers=onboarded_user["headers"])
        assert response.status_code == 200
        assert response.json()["preferences"] == {"notifications": False}

    @pytest.mark.asyncio
    async def test_preferences_are_replaced_not_merged(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        await client.patch(
            PROFILE_ME_URL,
            json={"preferences": {"theme": "dark", "lang": "en"}},
            headers=onboarded_user["headers"],
        )
        await client.patch(
            PROFILE_ME_URL,
            json={"preferences": {"lang": "fr"}},
            headers=onboarded_user["headers"],
        )
        response = await client.get(PROFILE_ME_URL, headers=onboarded_user["headers"])
        assert response.status_code == 200
        assert response.json()["preferences"] == {"lang": "fr"}


class TestOnboarding:
    @pytest.mark.asyncio
    async def test_onboards_user_and_creates_profile(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        email = f"fresh-{uuid.uuid4().hex[:12]}@example.com"
        reg = await client.post(
            REGISTER_URL,
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "display_name": "Fresh User",
            },
        )
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        response = await client.post(
            ONBOARDING_URL,
            json={
                "display_name": "Fresh User",
                "bio": "My bio",
                "website": "https://example.com",
                "location": "NYC",
                "preferences": {"theme": "dark"},
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Fresh User"
        assert data["bio"] == "My bio"
        assert data["website"] == "https://example.com"
        assert data["location"] == "NYC"
        assert data["preferences"] == {"theme": "dark"}

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        response = await client.post(
            ONBOARDING_URL, json={"display_name": "No Auth"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_double_onboarding_returns_updated_profile(
        self,
        client: httpx.AsyncClient,
        onboarded_user: dict,
    ) -> None:
        response = await client.post(
            ONBOARDING_URL,
            json={
                "display_name": "Re-onboarded",
                "bio": "Updated during re-onboarding",
            },
            headers=onboarded_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Re-onboarded"
        assert data["bio"] == "Updated during re-onboarding"






