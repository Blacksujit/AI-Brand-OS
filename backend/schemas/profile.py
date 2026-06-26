from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    display_name: str
    email: str
    avatar_url: str | None = None
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] = {}
    created_at: str
    updated_at: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=128)
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] | None = None


class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] = {}
